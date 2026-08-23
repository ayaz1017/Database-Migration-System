import React from 'react'
import { Link } from 'react-router-dom'
import { Database, ArrowRight } from 'lucide-react'

const GithubIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
  </svg>
)

const TwitterIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
  </svg>
)

const LinkedinIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
  </svg>
)

const FOOTER_LINKS = {
  Product: [
    { name: 'Migration Engine', href: '/docs' },
    { name: 'AST Translator', href: '/sandbox' },
    { name: 'Architecture', href: '/architecture' },
    { name: 'Pricing', href: '/pricing' },
    { name: 'Documentation', href: '/docs' },
  ],
  Dialects: [
    { name: 'PostgreSQL 14–17', href: '/docs' },
    { name: 'MySQL 8.0 & Aurora', href: '/docs' },
    { name: 'Microsoft SQL Server', href: '/docs' },
    { name: 'Oracle Database 19c/21c', href: '/docs' },
  ],
  Solutions: [
    { name: 'Zero-Downtime CDC', href: '/docs' },
    { name: 'Data Masking & PII', href: '/docs' },
    { name: 'Multi-Tenant Partitioning', href: '/docs' },
    { name: 'Air-Gapped Deployments', href: '/pricing' },
  ],
  Company: [
    { name: 'Changelog', href: '/docs' },
    { name: 'Privacy Policy', href: '#' },
    { name: 'Terms of Service', href: '#' },
    { name: 'Security & Compliance', href: '#' },
  ]
}

export default function MarketingFooter() {
  return (
    <footer className="w-full bg-[#070709] border-t border-zinc-800/80 pt-16 pb-10">
      <div className="max-w-[1360px] mx-auto px-6 md:px-10">
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-10 lg:gap-8 mb-14">
          
          {/* Brand & Newsletter Column */}
          <div className="lg:col-span-2">
            <Link to="/" className="flex items-center space-x-2.5 mb-4">
              <div className="w-7 h-7 rounded-md bg-zinc-900 border border-zinc-700 flex items-center justify-center text-indigo-400">
                <Database className="w-3.5 h-3.5" />
              </div>
              <span className="font-sans text-base font-bold tracking-tight text-white">Fluxline</span>
            </Link>
            <p className="font-sans text-xs text-zinc-400 leading-relaxed mb-6 pr-4">
              Deterministic cross-dialect database migration engine. Type-safe AST translation, keyset chunking, and live CDC log tailing with byte checksum verification.
            </p>
            
            {/* Newsletter / Updates */}
            <div className="max-w-sm">
              <h4 className="font-sans text-xs font-semibold text-zinc-300 mb-2">Engine Updates & Changelogs</h4>
              <div className="flex relative">
                <input 
                  type="email" 
                  placeholder="name@company.com" 
                  className="w-full bg-zinc-900/80 border border-zinc-800 rounded-md py-2 pl-3 pr-10 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-indigo-500/60 focus:bg-zinc-900 transition-colors"
                />
                <button className="absolute right-1 top-1 bottom-1 px-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded text-xs transition-colors flex items-center justify-center cursor-pointer">
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Link Columns */}
          {Object.entries(FOOTER_LINKS).map(([title, links]) => (
            <div key={title} className="lg:col-span-1">
              <h4 className="font-sans text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-4">{title}</h4>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.name}>
                    <Link to={link.href} className="font-sans text-xs text-zinc-400 hover:text-zinc-200 transition-colors">
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-zinc-800/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-mono text-zinc-400">All services operational • AST Engine v2.4</span>
          </div>
          
          <div className="text-zinc-500">
            &copy; {new Date().getFullYear()} Fluxline Systems Inc. All rights reserved.
          </div>

          <div className="flex items-center space-x-3 text-zinc-500">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-zinc-300 transition-colors">
              <GithubIcon />
            </a>
            <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="hover:text-zinc-300 transition-colors">
              <TwitterIcon />
            </a>
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="hover:text-zinc-300 transition-colors">
              <LinkedinIcon />
            </a>
          </div>
        </div>

      </div>
    </footer>
  )
}
