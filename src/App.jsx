import React from 'react'
import Navbar from './components/Navbar';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css';
import './index.css';
import Home from './components/pages/Home'
import PhotosPage from './components/pages/PhotosPage'
import Contact from './components/pages/Contact';
import SouthKorea from './components/pages/SouthKorea';
import SouthAfrica from './components/pages/SouthAfrica';
import AlbumPage from './components/pages/AlbumPage';
import Footer from './components/Footer';


function App() {

  return (
    <>
      <div className='main__container'>
        <Router>
          <Navbar />
          <div className="content__container">
            <Routes>
              <Route path='/' element={<Home />} />
              <Route path='/photos' element={<PhotosPage />} />
              <Route path='/contact' element={<Contact />} />
              <Route path='/southkorea' element={<SouthKorea />} />
              <Route path='/southafrica' element={<SouthAfrica />} />

              {/* Dynamically add routes from the S3 bucket folders */}
              <Route
                path="/photos/:folder"
                loader={({ params }) => {
                  console.log(params.folder);
                }}
                action={({ params }) => { }}
                element={<AlbumPage />}
              />
            </Routes>
          </div>
          <Footer />
        </Router>
      </div>

    </>
  );
}

export default App;
