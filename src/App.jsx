import React from 'react';
import Navbar from './components/Navbar';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import './index.css';
import Home from './components/pages/Home';
import PhotosPage from './components/pages/PhotosPage';
import Contact from './components/pages/Contact';
import AlbumPage from './components/pages/AlbumPage';
import Footer from './components/Footer';

function App() {
  return (
    <div className="main__container">
      <Router basename={process.env.PUBLIC_URL}>
        <Navbar />
        <div className="content__container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/photos" element={<PhotosPage />} />
            {/* Albums come from photos.json */}
            <Route path="/photos/:slug" element={<AlbumPage />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </div>
        <Footer />
      </Router>
    </div>
  );
}

export default App;
