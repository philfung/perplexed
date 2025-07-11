import React, { useEffect, useState } from 'react';
import { Constants } from './constants';
import { Defaults } from './defaults';
import ReactMarkdown from 'react-markdown'
import './App.css';
import { Facebook } from "react-content-loader"


const SearchStage = {
  STARTING: "Starting search",
  QUERIED_GOOGLE: "Querying Google",
  DOWNLOADED_WEBPAGES: "Downloading Webpages",
  QUERIED_LLM: "Querying LLM",
  RESULTS_READY: "Results ready"
};

class WebSearchDocument {
  constructor(id, title, url, text = '') {
    this.id = id;
    this.title = title;
    this.url = url;
    this.text = text;
  }
};

class SearchResponse {
  constructor(success, stage, num_tokens_used, websearch_docs, answer, error_message = '') {
    this.success = success;
    this.stage = stage;
    this.num_tokens_used = num_tokens_used;
    this.websearch_docs = websearch_docs;
    this.answer = answer;
    this.error_message = error_message;
  }
};

// Sidebar component for desktop layout

function App() {
  const [userPrompt, setUserPrompt] = useState('');
  const [searchResponse, setSearchResponse] = useState(null);

  const resetSearch = async () => {
    setUserPrompt('');
    setSearchResponse(null);
  };

  function goHome() {
    resetSearch();
    window.scrollTo(0, 0);
    window.location.reload();
  }

  const Sidebar = () => {
    return (
      <div className="sidebar hidden md:flex flex-col bg-pp-bg-light-grey border-r border-pp-border-grey  w-[170px] h-screen fixed left-0 top-0">
        <div className="logo-container flex justify-center items-center h-header-height border-b border-gray-800 pr-1 py-4"
             onClick={() => { goHome(); }}>
          <img className="h-8 mt-2 w-1/4" src={process.env.PUBLIC_URL + "/images/logo-color.svg"} alt="logo" />
          <div className="font-extralight select-none text-2xl text-pp-text-white">{Defaults.appDisplayName}</div>
        </div>
      </div>
    );
  };
  

  const submitSearch = async (submittedUserPrompt) => {
    // console.log("SUBMISEARCH:" + submittedUserPrompt);
    setUserPrompt(submittedUserPrompt);
  
    let res = null;
    let error_message = '';

    try {

      res = await fetch(Constants.API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_prompt: submittedUserPrompt })
      });

    } catch (error) {
      console.log("Error submitting search: " + error);
      error_message = 'We\'re experiencing a high volume of requests at the moment. Please try again in a little while. We apologize for the inconvenience.';
    }
    if (!res || !res.ok) {
      console.log('Stream response not ok');
      setSearchResponse(new SearchResponse(
        false,
        null,
        0,
        [],
        '',
        error_message
      ));
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');

    let buffer = '';

    reader.read().then(function processText({ done, value }) {
      if (done) {
        console.log('Stream complete');
        return;
      }
      // console.log("processText");
      // console.log(decoder.decode(value));

      buffer += decoder.decode(value);
      let boundary = buffer.indexOf(Constants.JSON_STREAM_SEPARATOR);
      while (boundary !== -1) {
        let input = buffer.substring(0, boundary);
        buffer = buffer.substring(boundary + Constants.JSON_STREAM_SEPARATOR.length);
        if (input.trim() === '') {
          return;
        }
        let result = JSON.parse(input);
        boundary = buffer.indexOf(Constants.JSON_STREAM_SEPARATOR);

        const isSuccess = result.success;
        const error_message = isSuccess ? '' : result.message;

        if (isSuccess) {
          setSearchResponse(new SearchResponse(
            isSuccess,
            result.stage,
            result.num_tokens_used,
            result.websearch_docs.map(doc => new WebSearchDocument(doc.id, doc.title, doc.url, doc.text)),
            result.answer
          ));
        } else {
          setSearchResponse(new SearchResponse(
            isSuccess,
            null,
            0,
            [],
            '',
            error_message
          ));
          console.log('Error:', error_message);
          return;
        };
      }

      reader.read().then(processText);
    });
  };

  function getDomainasWord(url) {
    const hostname = new URL(url).hostname;
    const parts = hostname.split('.');
    return parts.length > 1 ? parts[parts.length - 2] : parts[0];
  }

  function getFaviconUrl(url) {
    const parsedUrl = new URL(url);
    return parsedUrl.protocol + "//" + parsedUrl.hostname + "/favicon.ico";
  }

  let searchExamples = Defaults.searchExamples;

  return (
    <div className="App">
      {/* Sidebar component */}
      <Sidebar />
      
      {!userPrompt &&
        <div className="input-page bg-pp-bg-dark-grey flex flex-col h-screen md:ml-[170px]">
          <div className="header border-b border-gray-800 flex flex-row h-header-height items-center justify-between ml-8 mr-8 md:hidden">
            <div className="logo-container flex flex-row">
              <img className="App-logo flex h-9 mt-1 mr-1" src={process.env.PUBLIC_URL + "/images/logo-color.svg"} alt="logo" />
              <div className="header-text flex font-extralight select-none text-3xl text-pp-text-white">{Defaults.appDisplayName}</div>
            </div>
            <a className="flex" href={Constants.GITHUB_LINK} target="_blank" rel="noopener noreferrer">
              <img className="github flex opacity-50 w-10" src={process.env.PUBLIC_URL + "/images/github_logo.png"} />
            </a>
          </div>
          <div className="main-center-stuff flex flex-col mx-9 mt-8 md:mt-32 md:mx-20">
              <div className="welcome-slogan flex font-light font-fkgr mb-8 md:justify-center select-none text-3xl md:text-4xl text-pp-text-white">{Defaults.appUserPrompt}</div>
            <div className="search-input-container bg-pp-bg-light-grey border border-pp-border-grey flex flex-col pl-4 pr-2 pt-4 pb-2 rounded-3xl">
              <textarea id="search-input" className="bg-transparent flex focus:outline-none focus:shadow-outline-none font-fkgrneue font-light h-12 placeholder-pp-text-grey text-16 text-pp-text-white"
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    console.log(e);
                    submitSearch(e.target.value);
                  }
                }}
                placeholder='Ask anything...'>
              </textarea>
              <div className="search-lower-bar flex flex-row justify-end">
                <div className="search-lower-bar-arrow bg-pp-button-grey flex flex-row w-8 h-8  rounded-full">
                  <img className="search-submit-button mx-auto w-5" src={process.env.PUBLIC_URL + '/images/arrow_submit.svg'} alt="submit"
                    onClick={() => { submitSearch(document.getElementById('search-input').value); }}
                  />
                </div>
              </div>
            </div>
            <div className="search-examples flex flex-row flex-wrap mt-7">
              {searchExamples.map((example, i) => (
                <div key={i} className="search-example border border-gray-900 flex flex-row items-center mx-1 my-1 rounded-full"
                  onClick={() => { submitSearch(example.text); }}
                >
                  <div className="search-example-emoji ml-1">{example.emoji}</div>
                  <div className="search-example-text font-fkgr inline-block ml-2 mr-1 text-sm text-gray-500">{example.text}</div>
                </div>
              ))
              }

            </div>
          </div>

        </div>
      }
      {
        userPrompt &&
        <div className="results-page bg-pp-bg-dark-grey min-h-screen md:ml-[170px]">
          <div className="header border-b border-gray-800 flex flex-row h-11 items-center justify-between pl-3 md:hidden" >
            <div className="logo-container flex flex-row" onClick={() => { goHome(); }}>
              <img className="logo-white flex h-7"  
                   src={process.env.PUBLIC_URL + "/images/logo-color.svg"} alt="logo" />
              <div className="flex font-extralight ml-1 select-none text-xl text-pp-text-white">{Defaults.appDisplayName}</div>
            </div>
            <a className="flex" href={Constants.GITHUB_LINK} target="_blank" rel="noopener noreferrer">
              <img className="github flex opacity-50 mr-4 w-7" src={process.env.PUBLIC_URL + "/images/github_logo.png"} />
            </a>
          </div>
          <div className="results-container px-4 md:px-16 md:pt-2">
            {(!searchResponse || (searchResponse && searchResponse.success)) &&
              <div className="query font-light font-fkgr mt-8 mb-3 select-none text-3xl text-pp-text-white">{userPrompt}</div>
            }
            {!searchResponse &&
                <div className="sources">

                  <div className="sources-header animate-pulse bg-pp-bg-light-grey flex flex-row h-7 items-center opacity-90 mx-1 mb-2 rounded-md w-20">
                    <div className="sources-header-text flex font-regular font-fkgr ml-2 text-lg text-pp-text-white "></div>
                  </div>
                  <div className="sources-results flex flex-row flex-wrap">
                    {
                      [1, 2, 3, 4].map((doc, i) => (
                        <div className="source-result animate-pulse bg-pp-bg-light-grey flex-col h-10 m-1 opacity-90 px-2 py-3 rounded-md w-width-percent-45">
                        </div>
                      ))
                    }
                  </div>
                </div>
            }
            {
              searchResponse && !searchResponse.success &&
              <div className="error font-light font-fkgr mt-14 text-xl text-red-500">
                {
                  searchResponse.error_message ?
                    searchResponse.error_message
                    : "Error processing search, please try again."
                }</div>
            }
            {searchResponse && searchResponse.success &&
              searchResponse.websearch_docs &&
              searchResponse.websearch_docs.length > 0 &&
              <div className="sources">
                <div className="sources-header flex flex-row items-center mb-2">
                  <div className="sources-header-icon flex h-5"><img src={process.env.PUBLIC_URL + "/images/sources-icon.svg"} /></div>
                  <div className="sources-header-text flex font-regular font-fkgr ml-2 text-lg text-pp-text-white ">Sources</div>
                </div>
                <div className="sources-results flex flex-row flex-wrap">
                  {
                    searchResponse.websearch_docs.map((doc, i) => (
                      <div key={i} className="source-result bg-pp-bg-light-grey flex-col m-1 px-2 py-3 rounded-md w-width-percent-45">
                        <a className="source-link flex font-fkgrneue max-h-8 overflow-hidden text-xs text-pp-text-white" href={doc.url} rel="noopener noreferrer" target="_blank" >{doc.title}</a>
                        <div className="source-result-bottom text-gray-500 flex flex-row font-fkgr items-center mt-2 text-xs">
                          <img className="favicon flex h-3" src={getFaviconUrl(doc.url)}
                            onError={(e) => { e.target.onerror = null; e.target.src = process.env.PUBLIC_URL + "/images/earth-blue.svg"; }}
                          />
                          <div className="website flex ml-2">{getDomainasWord(doc.url)}</div>
                          <div className="number flex ml-1">{"• " + (i + 1)}</div>
                        </div>
                      </div>
                    ))
                  }
                </div>
              </div>
            }
            {
              searchResponse && searchResponse.success && !searchResponse.answer &&
              <div className="results-loader animate-pulse opacity-50 ml-1 mt-8 w-3/4">
                <Facebook animate={true} speed={2} />
              </div>
            }
            {searchResponse && searchResponse.success && searchResponse.answer &&
              <div className="answer mt-5">
                <div className="answer-header flex flex-row items-center mb-2">
                  <div className="answer-header-icon flex h-6"><img src={process.env.PUBLIC_URL + "/images/logo-color.svg"} /></div>
                  <div className="answer-header-text flex font-regular font-fkgr ml-1 text-lg text-pp-text-white ">Answer</div>
                </div>
                <div className="answer-text font-extralight font-fkgrneue pb-20 text-md text-pp-text-white">{
                  <ReactMarkdown>
                    {searchResponse.answer}
                  </ReactMarkdown>
                }</div>
              </div>
            }
            {
              <div className="new-search bg-pp-bg-light-grey border border-gray-600 bottom-2 fixed flex flex-row h-14 items-center left-1/2 rounded-full text-gray-500 text-lg transform -translate-x-1/2 w-11/12 md:w-8/12 md:left-[calc(50%+70px)]">
                <button className="ml-10" onClick={() => { resetSearch(); }}>Ask follow-up..</button>
              </div>
            }
          </div>
        </div>
      }

    </div>
  );
}

export default App;
