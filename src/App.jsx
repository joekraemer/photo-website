import React from 'react'
import Navbar from './components/Navbar';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css';
import './index.css';
import Home from './components/pages/Home'
import PhotosPage from './components/pages/PhotosPage'
import Contact from './components/pages/Contact';

function App() {
  return (
    <>
      <div className='main__container'>
        <Router>
          <Navbar />
          <Routes>
            <Route path='/' element={<Home />} />
            <Route path='/photos' element={<PhotosPage />} />
            <Route path='/contact' element={<Contact />} />
          </Routes>
        </Router>
      </div>

    </>
  );
}

export default App;
