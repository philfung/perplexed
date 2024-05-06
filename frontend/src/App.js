import React, { useState } from 'react';
import { Constants } from './constants';
import ReactMarkdown from 'react-markdown'
import logo from './logo.svg';
import './App.css';

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

function App() {
  const [userPrompt, setUserPrompt] = useState('');
  const [searchResponse, setSearchResponse] = useState(null);

  const resetSearch = async () => {
    setUserPrompt('');
    setSearchResponse(null);
  };

  const submitSearch = async (submittedUserPrompt) => {
    console.log("SUBMISEARCH:" + submittedUserPrompt);
    setUserPrompt(submittedUserPrompt);
    const res = await fetch(Constants.API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_prompt: submittedUserPrompt })
    }); const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');

    reader.read().then(function processText({ done, value }) {
      if (done) {
        console.log('Stream complete');
        return;
      }
      const result = JSON.parse(decoder.decode(value));
      const isSuccess = result.success;
      const error_message = isSuccess ? '' : result.message;

      console.log(result);

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
      reader.read().then(processText);
    });
  };

  return (
    <div className="App">
      {!userPrompt &&

        <div className="input-page">
          <div>Enter your search query:</div>
          {<input name="search-input" type="text"
            onKeyDown={e => {
              if (e.key === 'Enter') {
                console.log(e);
                submitSearch(e.target.value);
              }
            }}

          />}
        </div>
      }
      {
        userPrompt &&
        <div className="results-page">
          <div className="header">{userPrompt}</div>
          {
            searchResponse && !searchResponse.success &&
            <div className="error">
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
              <div className="sources-header">Sources</div>
              {
                searchResponse.websearch_docs.map((doc, i) => (
                  <div key={i} className="source">
                    <a href={doc.url} target="_blank" rel="noopener noreferrer" className="link">{doc.title}</a>
                  </div>
                ))
              }
            </div>
          }
          {searchResponse && searchResponse.success && searchResponse.answer &&
            <div className="answer">
              <div className="answer-header">Answer</div>
              <div className="answer-text">{
                <ReactMarkdown>
                  {searchResponse.answer}
                </ReactMarkdown>
              }</div>
            </div>
          }
          {
            <div className="new-search">
              <button onClick={() => {resetSearch();}}>New Search</button>
            </div>
          }

        </div>
      }

    </div>
  );
}

export default App;
