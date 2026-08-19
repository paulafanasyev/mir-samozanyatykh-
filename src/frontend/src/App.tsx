import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { lazy, Suspense, useEffect } from 'react'
import Layout from './components/Layout'
import { useAuthStore } from './stores/authStore'

const Home = lazy(() => import('./pages/Home'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Products = lazy(() => import('./pages/Products'))
const Invoices = lazy(() => import('./pages/Invoices'))
const Clients = lazy(() => import('./pages/Clients'))
const Deals = lazy(() => import('./pages/Deals'))
const Contracts = lazy(() => import('./pages/Contracts'))
const Profile = lazy(() => import('./pages/Profile'))
const Svetlana = lazy(() => import('./pages/Svetlana'))
const Tasks = lazy(() => import('./pages/Tasks'))
const CalendarPage = lazy(() => import('./pages/CalendarPage'))
const Integrations = lazy(() => import('./pages/Integrations'))
const DocsPage = lazy(() => import('./pages/DocsPage'))
const Accounting = lazy(() => import('./pages/Accounting'))
const TaxReports = lazy(() => import('./pages/TaxReports'))
const ReceiptCheck = lazy(() => import('./pages/ReceiptCheck'))
const EmailCampaigns = lazy(() => import('./pages/EmailCampaigns'))
const AdminPanel = lazy(() => import('./pages/AdminPanel'))
const AuditLogs = lazy(() => import('./pages/AuditLogs'))
const Referrals = lazy(() => import('./pages/Referrals'))
const Notifications = lazy(() => import('./pages/Notifications'))
const Downloads = lazy(() => import('./pages/Downloads'))

const PageLoader = () => <div className='flex items-center justify-center min-h-screen'><div className='animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600' /></div>

function AuthBootstrap() {
  const hydrate = useAuthStore((s) => s.hydrate)
  useEffect(() => { void hydrate() }, [hydrate])
  return <Outlet />
}

function ProtectedLayout() {
  const { hydrated, user } = useAuthStore()
  if (!hydrated) return <PageLoader />
  if (!user) return <Navigate to='/login' replace />
  return <Layout />
}

function AdminGuard() {
  const { hydrated, user } = useAuthStore()
  if (!hydrated) return <PageLoader />
  if (!user) return <Navigate to='/login' replace />
  if (!user.is_admin && !user.is_moderator) return <Navigate to='/dashboard' replace />
  return <Outlet />
}

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route element={<AuthBootstrap />}>
          <Route path='/' element={<Home />} />
          <Route path='/login' element={<Login />} />
          <Route path='/register' element={<Register />} />
          <Route path='/verify-email' element={<VerifyEmail />} />
          <Route path='/reset-password' element={<ResetPassword />} />
          <Route path='/downloads' element={<Downloads />} />
          <Route element={<ProtectedLayout />}>
            <Route path='/dashboard' element={<Dashboard />} />
            <Route path='/products' element={<Products />} />
            <Route path='/invoices' element={<Invoices />} />
            <Route path='/clients' element={<Clients />} />
            <Route path='/deals' element={<Deals />} />
            <Route path='/contracts' element={<Contracts />} />
            <Route path='/profile' element={<Profile />} />
            <Route path='/svetlana' element={<Svetlana />} />
            <Route path='/tasks' element={<Tasks />} />
            <Route path='/calendar' element={<CalendarPage />} />
            <Route path='/integrations' element={<Integrations />} />
            <Route path='/docs' element={<DocsPage />} />
            <Route path='/accounting' element={<Accounting />} />
            <Route path='/tax-reports' element={<TaxReports />} />
            <Route path='/receipt-check' element={<ReceiptCheck />} />
            <Route path='/email-campaigns' element={<EmailCampaigns />} />
            <Route path='/referrals' element={<Referrals />} />
            <Route path='/notifications' element={<Notifications />} />
            <Route element={<AdminGuard />}>
              <Route path='/admin' element={<AdminPanel />} />
              <Route path='/admin/audit-logs' element={<AuditLogs />} />
            </Route>
          </Route>
          <Route path='*' element={<Navigate to='/' replace />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
