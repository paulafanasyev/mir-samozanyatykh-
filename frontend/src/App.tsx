import { Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Layout from './components/Layout'

// Lazy-loaded pages
const Home = lazy(() => import('./pages/Home'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Products = lazy(() => import('./pages/Products'))
const Invoices = lazy(() => import('./pages/Invoices'))
const Clients = lazy(() => import('./pages/Clients'))
const Deals = lazy(() => import('./pages/Deals'))
const Contracts = lazy(() => import('./pages/Contracts'))
const Profile = lazy(() => import('./pages/Profile'))
const Svetlana = lazy(() => import('./pages/Svetlana'))

const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
)

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="products" element={<Products />} />
          <Route path="invoices" element={<Invoices />} />
          <Route path="clients" element={<Clients />} />
          <Route path="deals" element={<Deals />} />
          <Route path="contracts" element={<Contracts />} />
          <Route path="profile" element={<Profile />} />
          <Route path="svetlana" element={<Svetlana />} />
          <Route path="admin" element={<AdminPanel />} />
          <Route path="admin/audit-logs" element={<AuditLogs />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
