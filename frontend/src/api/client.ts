import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization Bearer token to all outgoing API requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('cms_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Intercept error responses for clean consistent handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ code?: string; message?: string }>) => {
    if (error.response?.status === 401) {
      const token = localStorage.getItem('cms_access_token');
      const isDemo = token?.startsWith('demo-token-');
      if (!isDemo) {
        // Clear token and redirect to login if session expired
        localStorage.removeItem('cms_access_token');
        localStorage.removeItem('cms_user_profile');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      } else {
        console.warn('Demo session 401 received:', error.response?.data);
      }
    }
    return Promise.reject(error);
  }
);

// ----------------------------------------------------------------------
// Typed API Endpoints
// ----------------------------------------------------------------------

export const api = {
  // Auth & Profile
  me: () => apiClient.get('/me'),
  updateProfile: (data: { full_name?: string; phone?: string }) => apiClient.patch('/me', data),
  registerProfile: (data: {
    auth_user_id?: string;
    email?: string;
    full_name: string;
    phone?: string;
    role: string;
    trade_specialization?: string;
    desk_location?: string;
    badge_id?: string;
    property_id?: string;
    block_id?: string;
    new_property_number?: string;
    relationship_type?: string;
    admin_passcode?: string;
  }) => apiClient.post('/auth/register-profile', data),

  // Master Data
  getBlocks: () => apiClient.get('/blocks'),
  getProperties: (blockId?: string) => apiClient.get('/properties', { params: { block_id: blockId } }),
  createProperty: (data: {
    block_id: string;
    property_number: string;
    property_type?: string;
    address_note?: string;
    is_active?: boolean;
  }) => apiClient.post('/properties', data),
  getCategories: () => apiClient.get('/categories'),

  // Complaints
  getComplaints: (params?: { page?: number; page_size?: number; status?: string; category_id?: string; is_urgent?: boolean }) =>
    apiClient.get('/complaints', { params }),
  getComplaint: (id: string) => apiClient.get(`/complaints/${id}`),
  createComplaint: (data: { property_id: string; category_id: string; description: string; is_urgent?: boolean; urgency_reason?: string }) =>
    apiClient.post('/complaints', data),
  createOfflineComplaint: (data: {
    resident_id: string;
    property_id: string;
    category_id: string;
    description: string;
    is_urgent?: boolean;
    urgency_reason?: string;
    intake_channel: string;
  }) => apiClient.post('/complaints/offline', data),
  confirmComplaintResolution: (id: string, outcome: 'confirmed' | 'rejected', feedback?: string) =>
    apiClient.post(`/complaints/${id}/confirmations`, { outcome, feedback }),

  // Incidents
  getIncidents: (params?: { page?: number; page_size?: number; status?: string; category_id?: string }) =>
    apiClient.get('/incidents', { params }),
  getIncident: (id: string) => apiClient.get(`/incidents/${id}`),
  createIncident: (data: { category_id: string; title: string; description: string; priority?: string; area_description?: string; complaint_ids?: string[] }) =>
    apiClient.post('/incidents', data),
  updateIncidentStatus: (id: string, status: string, reason?: string) =>
    apiClient.patch(`/incidents/${id}/status`, { status, reason }),
  linkComplaint: (incidentId: string, complaintId: string, overrideMismatch = false) =>
    apiClient.post(`/incidents/${incidentId}/links`, { complaint_id: complaintId, override_category_mismatch: overrideMismatch }),
  unlinkComplaint: (incidentId: string, linkId: string, unlinkReason: string) =>
    apiClient.delete(`/incidents/${incidentId}/links/${linkId}`, { data: { unlink_reason: unlinkReason } }),

  // Work Assignments
  getAssignments: (params?: { page?: number; page_size?: number; status?: string }) =>
    apiClient.get('/assignments', { params }),
  assignStaff: (incidentId: string, staffProfileId: string, notes?: string) =>
    apiClient.post(`/incidents/${incidentId}/assignments`, { staff_profile_id: staffProfileId, notes }),
  updateAssignment: (id: string, status: string, notes?: string, completionNotes?: string) =>
    apiClient.patch(`/assignments/${id}`, { status, notes, completion_notes: completionNotes }),

  // External Utilities
  getUtilityCompanies: () => apiClient.get('/utilities/companies'),
  getUtilityCases: (params?: { page?: number; page_size?: number; overdue_only?: boolean }) =>
    apiClient.get('/utility-cases', { params }),
  createUtilityCase: (incidentId: string, data: { utility_company_id: string; external_reference_number?: string; expected_resolution_at?: string; notes?: string }) =>
    apiClient.post(`/incidents/${incidentId}/utility-cases`, data),
  addUtilityUpdate: (caseId: string, data: { direction: string; update_type: string; message: string; provider_event_at?: string }) =>
    apiClient.post(`/utility-cases/${caseId}/updates`, data),

  // Dashboard & Analytics
  getDashboardSummary: () => apiClient.get('/dashboard/summary'),
  getRecurringFaults: (days = 90) => apiClient.get('/reports/recurring-faults', { params: { days } }),
  getStaffWorkload: () => apiClient.get('/reports/staff-workload'),
  getUtilityPerformance: () => apiClient.get('/reports/utility-response-times'),

  // Administration
  getUsers: (params?: { page?: number; role?: string }) => apiClient.get('/admin/users', { params }),
  getPropertyOccupancy: (blockId?: string) => apiClient.get('/admin/properties/occupancy', { params: { block_id: blockId } }),
  verifyResident: (residentId: string, status: 'verified' | 'rejected') =>
    apiClient.post(`/admin/residents/${residentId}/verify`, { verification_status: status }),
  associatePropertyResident: (data: {
    resident_id: string;
    property_id: string;
    relationship_type: string;
    valid_from: string;
    valid_until?: string;
    is_primary_contact?: boolean;
  }) => apiClient.post('/admin/property-residents', data),
  updateUserRole: (profileId: string, role: string) =>
    apiClient.patch(`/admin/users/${profileId}/role`, { role }),
  getAuditLogs: (params?: { page?: number; entity_type?: string }) =>
    apiClient.get('/admin/audit-logs', { params }),

  // Attachments
  registerAttachment: (data: {
    entity_type: string;
    entity_id: string;
    file_name: string;
    storage_path: string;
    mime_type: string;
    file_size_bytes: number;
  }) => apiClient.post('/attachments', data),
  getAttachmentDownloadUrl: (id: string) => apiClient.get(`/attachments/${id}/url`),
};
