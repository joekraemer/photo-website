import React from 'react'
import Navbar from './components/Navbar';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css';
import './index.css';
import Home from './components/pages/Home'
import Photos from './components/pages/Photos'

function App() {
  return (
    <>
      <div className='main__container'>
        <Router>
          <Navbar />
          <Routes>
            <Route path='/' element={<Home />} />
            <Route path='/photos' element={<Photos />} />
          </Routes>
        </Router>
      </div>

    </>
  );
}

export default App;
