import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import { supabase } from './supabase';

export interface UserProfile {
  id: string;
  auth_user_id: string;
  role: 'administrator' | 'complaint_officer' | 'field_staff' | 'resident';
  full_name: string;
  phone?: string;
  email?: string;
  is_active: boolean;
}

export interface ResidentInfo {
  id: string;
  profile_id: string;
  verification_status: 'pending' | 'verified' | 'rejected';
  verified_at?: string;
  properties: Array<{
    property_id: string;
    property_number: string;
    block_code: string;
    relationship_type: string;
    is_primary_contact: boolean;
  }>;
}

interface AuthContextType {
  token: string | null;
  profile: UserProfile | null;
  resident: ResidentInfo | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, phone?: string) => Promise<void>;
  logout: () => Promise<void>;
  setDemoSession: (role: UserProfile['role'], token: string, profile: UserProfile, resident?: ResidentInfo) => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('cms_access_token'));
  const [profile, setProfile] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem('cms_user_profile');
    return saved ? JSON.parse(saved) : null;
  });
  const [resident, setResident] = useState<ResidentInfo | null>(() => {
    const saved = localStorage.getItem('cms_resident_info');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  const refreshProfile = async () => {
    if (!localStorage.getItem('cms_access_token')) {
      setLoading(false);
      return;
    }
    try {
      const res = await api.me();
      setProfile(res.data.profile);
      setResident(res.data.resident);
      localStorage.setItem('cms_user_profile', JSON.stringify(res.data.profile));
      if (res.data.resident) {
        localStorage.setItem('cms_resident_info', JSON.stringify(res.data.resident));
      }
    } catch (err) {
      console.error('Failed to load profile', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      if (data.session) {
        const accessToken = data.session.access_token;
        setToken(accessToken);
        localStorage.setItem('cms_access_token', accessToken);
        await refreshProfile();
      }
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string, phone?: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName, phone: phone || '' },
        },
      });
      if (error) throw error;
      if (data.session) {
        const accessToken = data.session.access_token;
        setToken(accessToken);
        localStorage.setItem('cms_access_token', accessToken);
        await refreshProfile();
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await supabase.auth.signOut();
    } catch {
      // Ignored
    }
    setToken(null);
    setProfile(null);
    setResident(null);
    localStorage.removeItem('cms_access_token');
    localStorage.removeItem('cms_user_profile');
    localStorage.removeItem('cms_resident_info');
  };

  // Demo session helper for easy role switching and automated testing
  const setDemoSession = (
    _role: UserProfile['role'],
    newToken: string,
    newProfile: UserProfile,
    newResident?: ResidentInfo
  ) => {
    setToken(newToken);
    setProfile(newProfile);
    setResident(newResident || null);
    localStorage.setItem('cms_access_token', newToken);
    localStorage.setItem('cms_user_profile', JSON.stringify(newProfile));
    if (newResident) {
      localStorage.setItem('cms_resident_info', JSON.stringify(newResident));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        profile,
        resident,
        loading,
        login,
        register,
        logout,
        setDemoSession,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
