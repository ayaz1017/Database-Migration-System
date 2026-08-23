import React, { useState } from 'react';
import apiClient from '../apiClient';
import toast from 'react-hot-toast';
import { Lock, Loader } from 'lucide-react';

export default function ChangePassword() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
      toast.success('Password changed successfully');
      setOldPassword('');
      setNewPassword('');
    } catch (error) {
      toast.error(error.data?.detail || 'Failed to change password');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-[#11141A] rounded-xl border border-white/10 p-6 shadow-xl">
      <h2 className="font-sans text-h3 font-bold text-white mb-6 flex items-center">
        <Lock className="w-5 h-5 mr-2 text-blue-500" />
        Change Password
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block font-sans text-body-sm font-medium text-gray-400 mb-1">Current Password</label>
          <input
            type="password"
            required
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            className="w-full bg-[#0A0C10] border border-white/10 rounded-md py-2 px-3 text-white focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block font-sans text-body-sm font-medium text-gray-400 mb-1">New Password</label>
          <input
            type="password"
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full bg-[#0A0C10] border border-white/10 rounded-md py-2 px-3 text-white focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full mt-4 flex justify-center py-2 px-4 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? <Loader className="w-5 h-5 animate-spin" /> : 'Update Password'}
        </button>
      </form>
    </div>
  );
}
