import React from 'react';
import Navbar from './components/Navbar';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import './index.css';
import Home from './components/pages/Home';
import PhotosPage from './components/pages/PhotosPage';
import Contact from './components/pages/Contact';
import AlbumPage from './components/pages/AlbumPage';
import { NotFound, Videos } from './components/pages/MessagePage';
import Footer from './components/Footer';
import ScrollToTop from './components/ScrollToTop';

function App() {
  return (
    <div className="main__container">
      <Router basename={import.meta.env.BASE_URL.replace(/\/$/, '')}>
        <ScrollToTop />
        <Navbar />
        <div className="content__container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/photos" element={<PhotosPage />} />
            {/* Albums come from photos.json */}
            <Route path="/photos/:slug" element={<AlbumPage />} />
            {/* Shareable link: the album with the lightbox open on one photo */}
            <Route path="/photos/:slug/:photoId" element={<AlbumPage />} />
            <Route path="/videos" element={<Videos />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
        <Footer />
      </Router>
    </div>
  );
}

export default App;
