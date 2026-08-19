import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

const savedTheme = localStorage.getItem('ms-theme')
document.documentElement.dataset.theme = savedTheme === 'dark' ? 'dark' : 'light'

const queryClient = new QueryClient({

defaultOptions: {

queries: {

staleTime: 5 * 60 * 1000, // 5 минут

retry: 1,

refetchOnWindowFocus: false,

},

},
})

ReactDOM.createRoot(document.getElementById('root')!).render(

<React.StrictMode>

<QueryClientProvider client={queryClient}>

<BrowserRouter>

<App />

<Toaster

position="top-right"

toastOptions={{

duration: 4000,

style: {

background: '#1a1a2e',

color: '#fff',

},

}}

/>

</BrowserRouter>

</QueryClientProvider>

</React.StrictMode>,
)
