import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Search from './components/Search';
import Theory from './components/Theory';
import GraphView from './components/GraphView';
import PaperDetail from './components/PaperDetail';
import RepositoryDetail from './components/RepositoryDetail';
import StatusBar from './components/StatusBar';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              Research Catalog
            </Link>
            <div className="nav-links">
              <Link to="/" className="nav-link">Dashboard</Link>
              <Link to="/search" className="nav-link">Search</Link>
              <Link to="/theory" className="nav-link">Theory</Link>
              <Link to="/graph" className="nav-link">Graph</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<Search />} />
            <Route path="/theory" element={<Theory />} />
            <Route path="/graph" element={<GraphView />} />
            <Route path="/paper/:id" element={<PaperDetail />} />
            <Route path="/repository/:id" element={<RepositoryDetail />} />
          </Routes>
        </main>

        <StatusBar />
      </div>
    </Router>
  );
}

export default App;
