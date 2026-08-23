import { useState, useEffect, useCallback } from 'react';
import apiClient from '../apiClient';
import toast from 'react-hot-toast';
import { Users, Mail, Plus, Loader, Shield, Trash2 } from 'lucide-react';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isInviting, setIsInviting] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Viewer');

  const fetchUsers = useCallback(async () => {
    try {
      const data = await apiClient.get('/auth/users');
      setUsers(data);
    } catch {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleInvite = async (e) => {
    e.preventDefault();
    setIsInviting(true);
    try {
      await apiClient.post('/auth/invite', {
        email,
        password,
        role
      });
      toast.success('User invited successfully');
      setEmail('');
      setPassword('');
      setRole('Viewer');
      fetchUsers();
    } catch (error) {
      toast.error(error.data?.detail || 'Failed to invite user');
    } finally {
      setIsInviting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-sans text-h1 font-bold text-white flex items-center">
          <Users className="w-6 h-6 mr-3 text-blue-500" />
          User Management
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="bg-[#11141A] rounded-xl border border-white/10 p-5">
            <h3 className="font-sans text-h3 font-semibold text-white mb-4 flex items-center">
              <Plus className="w-4 h-4 mr-2" /> Add New User
            </h3>
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block font-sans text-caption font-semibold text-gray-400 mb-1">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-[#0A0C10] border border-white/10 rounded-md py-2 pl-9 pr-3 text-white focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block font-sans text-caption font-semibold text-gray-400 mb-1">Initial Password</label>
                <input
                  type="text"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#0A0C10] border border-white/10 rounded-md py-2 px-3 text-white focus:ring-blue-500 focus:border-blue-500 text-sm"
                  placeholder="Set initial password"
                />
              </div>
              <div>
                <label className="block font-sans text-caption font-semibold text-gray-400 mb-1">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-[#0A0C10] border border-white/10 rounded-md py-2 px-3 text-white focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="Admin">Admin</option>
                  <option value="Member">Member</option>
                  <option value="Viewer">Viewer</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={isInviting}
                className="w-full mt-2 flex justify-center items-center py-2 px-4 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-sans font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isInviting ? <Loader className="w-4 h-4 animate-spin mr-2" /> : null}
                Create User
              </button>
            </form>
          </div>
        </div>

        <div className="md:col-span-2">
          <div className="bg-[#11141A] rounded-xl border border-white/10 overflow-hidden">
            {loading ? (
              <div className="p-8 flex justify-center">
                <Loader className="w-8 h-8 text-blue-500 animate-spin" />
              </div>
            ) : (
              <table className="min-w-full divide-y divide-white/5">
                <thead className="bg-[#1A1D24]">
                  <tr>
                    <th className="px-6 py-3 text-left font-sans text-caption font-medium text-gray-400 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left font-sans text-caption font-medium text-gray-400 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-right font-sans text-caption font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 bg-[#11141A]">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                            <span className="text-blue-400 font-medium text-lg">
                              {u.email.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div className="ml-4">
                            <div className="font-sans text-body-sm font-medium text-white">{u.email}</div>
                            <div className="text-xs text-gray-500 font-mono mt-0.5">{u.id.substring(0, 8)}...</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          u.role === 'Admin' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' : 
                          u.role === 'Member' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                          'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                        }`}>
                          <Shield className="w-3 h-3 mr-1 mt-0.5" />
                          {u.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-red-400 hover:text-red-300 transition-colors p-1 rounded hover:bg-red-400/10">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan="3" className="px-6 py-8 text-center text-gray-500 text-sm">
                        No users found in this organization.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
