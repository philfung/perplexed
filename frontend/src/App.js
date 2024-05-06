import React, { useState } from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  const [userPrompt, setUserPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [stage, setStage] = useState('');

  const search = async () => {
    const res = await fetch('http://127.0.0.1:5000/stream_search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_prompt: userPrompt })
    });    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');

    reader.read().then(function processText({ done, value }) {
      if (done) {
        console.log('Stream complete');
        return;
      }

      const result = JSON.parse(decoder.decode(value));
      setResponse(result.websearch_docs);
      setStage(result.stage);
      console.log(result);
      reader.read().then(processText);
    });
  };
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <input type="text" value={userPrompt} onChange={e => setUserPrompt(e.target.value)} />
        <button onClick={search}>Search1</button>
        <p>Stage: {stage}</p>
        <p>Response: {JSON.stringify(response)}</p>
      </header>
    </div>
  );
}

export default App;
