import { create } from 'zustand'

interface User { id:number; email:string; full_name:string|null; role:string; tier:string; is_admin:boolean; is_moderator:boolean }
interface AuthState {
  user:User|null;
  token:string|null;
  hydrated:boolean;
  setAuth:(u:User,t:string)=>void;
  setToken:(t:string|null)=>void;
  hydrate:()=>Promise<void>;
  logout:()=>void;
}

export const useAuthStore=create<AuthState>((set,get)=>({
  user:null,
  token:null,
  hydrated:false,
  setAuth:(user,token)=>set({user,token}),
  setToken:(token)=>set({token}),
  hydrate:async()=>{
    if (get().hydrated) return
    try {
      const { default: apiClient } = await import('../api/client')
      let token = get().token
      if (!token) {
        try {
          const refreshed = await apiClient.post('/api/auth/refresh')
          token = refreshed.data?.access_token || null
          if (token) set({token})
        } catch {
          token = null
        }
      }
      if (token) {
        try {
          const me = await apiClient.get('/api/users/me')
          set({user: me.data, token})
        } catch {
          set({user:null, token:null})
        }
      }
    } finally {
      set({hydrated:true})
    }
  },
  logout:()=>set({user:null,token:null}),
}))

try { localStorage.removeItem('auth-storage') } catch {}
