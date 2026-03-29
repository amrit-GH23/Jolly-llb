import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Articles from './pages/Articles'
import CaseAnalyzer from './pages/CaseAnalyzer'

function App() {
  return (
    <>
      <Navbar />
      <main className="page-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<CaseAnalyzer />} />
          <Route path="/articles" element={<Articles />} />
        </Routes>
      </main>
      <Footer />
    </>
  )
}

export default App
