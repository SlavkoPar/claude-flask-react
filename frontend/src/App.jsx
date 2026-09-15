import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import NavBar from './components/NavBar'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Groups from './pages/Groups'
import Group from './components/group/Group'
import Answers from './pages/Answers'
import AnswerForm from './pages/AnswerForm'
import Documents from './pages/Documents'
import DocumentForm from './pages/DocumentForm'
import SideBar from './components/sidebar/SideBar'

function Home() {
  const [count, setCount] = useState(0)

  return (
    <>
      <section id="center">
        {/* <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div> */}
        <div>
          <h1>Get started</h1>
          {/* <Chat /> */}
        </div>
        {/* <button
          type="button"
          className="counter"
          onClick={() => setCount((count) => count + 1)}
        >
          Count is {count}
        </button> */}
      </section>

      <section className="kard">

          {/* <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#documentation-icon"></use>
          </svg> */}
          <p>
            I used `Claude` for FrontEnd/BackEnd development, but also `claude-sonnet-5 & Anthropic Files API` on the Backend to find `Questions & Answers`.
          </p>
          <p>
            I tried to be `less specific` about `Claude`, trying to force Claude to ask me as many questions as possible, but I didn't really succeed.
          </p>
          <p>
            The app allows a company to create its Knowledge, uploading `pdf` files.
          </p>
          <p>
            `Q&A maintenance` allows maintaining of questions and answers that customers already asked and answered.
          </p>
          <p>
            Inside of right SideBar you can ask a question like: `remote controller`, and Claude-Sonnet will search upopaded `pdf` files
          </p>
      </section>


      <section id="next-steps">
      {/* <div id="social">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#social-icon"></use>
          </svg>
          <h2>Connect with us</h2>
          <p>Join the Vite community</p>
          <ul>
            <li>
              <a href="https://github.com/vitejs/vite" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#github-icon"></use>
                </svg>
                GitHub
              </a>
            </li>
            <li>
              <a href="https://chat.vite.dev/" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#discord-icon"></use>
                </svg>
                Discord
              </a>
            </li>
            <li>
              <a href="https://x.com/vite_js" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#x-icon"></use>
                </svg>
                X.com
              </a>
            </li>
            <li>
              <a href="https://bsky.app/profile/vite.dev" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#bluesky-icon"></use>
                </svg>
                Bluesky
              </a>
            </li>
          </ul>
        </div> */}
    </section >

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <>
      <NavBar onToggleSidebar={() => setSidebarOpen(o => !o)} />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/groups" element={<ProtectedRoute><Groups /></ProtectedRoute>} />
        <Route path="/groups/add" element={<ProtectedRoute><Group /></ProtectedRoute>} />
        <Route path="/groups/:id/edit" element={<ProtectedRoute><Group /></ProtectedRoute>} />
        <Route path="/answers" element={<ProtectedRoute><Answers /></ProtectedRoute>} />
        <Route path="/answers/add" element={<ProtectedRoute><AnswerForm /></ProtectedRoute>} />
        <Route path="/documents" element={<ProtectedRoute><Documents /></ProtectedRoute>} />
        <Route path="/documents/add" element={<ProtectedRoute><DocumentForm /></ProtectedRoute>} />
      </Routes>
      <SideBar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
    </>
  )
}

export default App
