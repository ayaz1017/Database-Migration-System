import React, { useState } from 'react';

const OracleSetupGuide = ({ username = 'YOUR_USER' }) => {
  const [isOpen, setIsOpen] = useState(false);

  const safeUsername = username ? username.toUpperCase() : 'YOUR_USER';

  if (!isOpen) {
    return (
      <div className="bg-yellow-500/10 border border-yellow-500/50 rounded-md p-3 my-4 flex items-start justify-between">
        <div className="flex items-start">
          <span className="text-yellow-500 mr-2">⚠️</span>
          <div>
            <p className="text-yellow-100 text-sm">
              Oracle target requires elevated privileges. Ensure your Oracle user has the required grants before migrating.
            </p>
          </div>
        </div>
        <button 
          onClick={() => setIsOpen(true)}
          className="text-yellow-400 hover:text-yellow-300 text-sm font-medium whitespace-nowrap ml-4 underline"
        >
          View Setup Guide
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[#1e1e1e] border border-gray-700 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-4 border-b border-gray-700 sticky top-0 bg-[#1e1e1e]">
          <h2 className="text-xl font-bold text-white">Oracle Setup Guide</h2>
          <button 
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>
        
        <div className="p-6 space-y-8 text-gray-300">
          <section>
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
              <span className="bg-blue-500/20 text-blue-400 w-6 h-6 rounded-full flex items-center justify-center text-sm mr-2">1</span>
              Oracle Target Setup (Required Privileges)
            </h3>
            <p className="text-sm mb-3">Run these commands as <strong>SYSDBA</strong> before migrating to Oracle:</p>
            <div className="bg-black rounded-md p-4 font-mono text-xs overflow-x-auto border border-gray-800">
              <span className="text-gray-500">-- Connect as SYSDBA</span><br/>
              <span className="text-blue-400">CONNECT</span> / <span className="text-purple-400">AS SYSDBA</span><br/><br/>
              
              <span className="text-gray-500">-- Grant privileges to your user</span><br/>
              <span className="text-blue-400">GRANT</span> <span className="text-green-400">CREATE SESSION</span> TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT</span> <span className="text-green-400">CREATE TABLE</span> TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT</span> <span className="text-green-400">CREATE SEQUENCE</span> TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT</span> <span className="text-green-400">CREATE TRIGGER</span> TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT</span> <span className="text-green-400">CREATE VIEW</span> TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT</span> <span className="text-green-400">CREATE PROCEDURE</span> TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT</span> <span className="text-green-400">CREATE INDEX</span> TO {safeUsername};<br/>
              <span className="text-blue-400">ALTER USER</span> {safeUsername} <span className="text-green-400">QUOTA UNLIMITED ON</span> USERS;<br/>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
              <span className="bg-blue-500/20 text-blue-400 w-6 h-6 rounded-full flex items-center justify-center text-sm mr-2">2</span>
              Verify Grants Worked
            </h3>
            <p className="text-sm mb-3">Run this as your migration user ({safeUsername}) to check your session privileges:</p>
            <div className="bg-black rounded-md p-4 font-mono text-xs overflow-x-auto border border-gray-800">
              <span className="text-blue-400">SELECT</span> * <span className="text-blue-400">FROM</span> SESSION_PRIVS;<br/>
              <span className="text-gray-500">-- Should show CREATE TABLE, CREATE SEQUENCE, etc.</span>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
              <span className="bg-blue-500/20 text-blue-400 w-6 h-6 rounded-full flex items-center justify-center text-sm mr-2">3</span>
              Oracle Source Setup
            </h3>
            <p className="text-sm mb-3">If you are migrating <strong>FROM</strong> Oracle, the connected user needs read access:</p>
            <div className="bg-black rounded-md p-4 font-mono text-xs overflow-x-auto border border-gray-800">
              <span className="text-blue-400">GRANT SELECT ANY TABLE TO</span> {safeUsername};<br/>
              <span className="text-blue-400">GRANT SELECT ANY DICTIONARY TO</span> {safeUsername};<br/><br/>
              <span className="text-gray-500">-- OR more restrictive:</span><br/>
              <span className="text-blue-400">GRANT SELECT ON</span> ALL_TABLES TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT SELECT ON</span> ALL_TAB_COLUMNS TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT SELECT ON</span> ALL_CONSTRAINTS TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT SELECT ON</span> ALL_TRIGGERS TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT SELECT ON</span> ALL_VIEWS TO {safeUsername};<br/>
              <span className="text-blue-400">GRANT SELECT ON</span> ALL_SEQUENCES TO {safeUsername};<br/>
            </div>
          </section>

          <section>
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
              <span className="bg-blue-500/20 text-blue-400 w-6 h-6 rounded-full flex items-center justify-center text-sm mr-2">4</span>
              Common Errors
            </h3>
            <div className="space-y-3">
              <div className="bg-[#2a2a2a] p-3 rounded-md border border-gray-700">
                <div className="font-mono text-red-400 text-sm font-semibold mb-1">ORA-01031</div>
                <div className="text-sm text-gray-400">Missing system privilege.</div>
                <div className="text-sm font-mono mt-1 text-gray-300">Fix: GRANT CREATE TABLE TO user;</div>
              </div>
              <div className="bg-[#2a2a2a] p-3 rounded-md border border-gray-700">
                <div className="font-mono text-red-400 text-sm font-semibold mb-1">ORA-01536</div>
                <div className="text-sm text-gray-400">Quota exceeded.</div>
                <div className="text-sm font-mono mt-1 text-gray-300">Fix: ALTER USER user QUOTA UNLIMITED ON tablespace;</div>
              </div>
              <div className="bg-[#2a2a2a] p-3 rounded-md border border-gray-700">
                <div className="font-mono text-yellow-400 text-sm font-semibold mb-1">ORA-00955</div>
                <div className="text-sm text-gray-400">Object already exists.</div>
                <div className="text-sm font-mono mt-1 text-gray-300">Fix: Fluxline handles this automatically.</div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default OracleSetupGuide;
