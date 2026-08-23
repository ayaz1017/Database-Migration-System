import sys

file_path = r'c:/Users/Ayaz Khan/Desktop/Database Migration Agent/frontend/src/pages/Landing.jsx'
with open(file_path, 'r', encoding='utf-8') as f: content = f.read()

content = content.replace('text-4xl md:text-6xl lg:text-[4.5rem] font-display font-extrabold', 'font-sans text-display font-bold')
content = content.replace('text-base md:text-xl text-gray-300 max-w-2xl mb-10 leading-relaxed font-normal', 'font-sans text-body-lg text-gray-300 max-w-2xl mb-10')

content = content.replace('text-2xl md:text-4xl font-display font-bold', 'font-sans text-h2 font-bold')
content = content.replace('text-3xl md:text-5xl font-display font-bold', 'font-sans text-h2 font-bold')
content = content.replace('text-3xl md:text-4xl font-display font-bold', 'font-sans text-h2 font-bold')

content = content.replace('text-gray-400 text-base md:text-lg', 'font-sans text-body text-text-secondary')
content = content.replace('text-gray-400 text-sm md:text-base', 'font-sans text-body text-text-secondary')
content = content.replace('text-gray-300 text-base leading-relaxed mb-6', 'font-sans text-body text-text-secondary mb-6')
content = content.replace('text-base md:text-lg text-gray-300 mb-8 max-w-xl mx-auto leading-relaxed', 'font-sans text-body text-text-secondary mb-8 max-w-xl mx-auto')

content = content.replace('text-xl font-bold text-white mb-3', 'font-sans text-h4 font-semibold text-white mb-3')
content = content.replace('text-gray-400 text-sm leading-relaxed', 'font-sans text-body-sm text-gray-400')

content = content.replace('text-xs font-bold font-mono', 'font-mono text-caption font-bold')
content = content.replace('text-xs font-mono font-bold', 'font-mono text-caption font-bold')

content = content.replace('text-white font-bold text-base mb-2', 'font-sans text-body font-semibold text-white mb-2')

content = content.replace('text-white font-bold transition-all', 'text-white font-sans font-semibold transition-all')
content = content.replace('text-white font-semibold border', 'text-white font-sans font-semibold border')
content = content.replace('text-black font-bold text-base hover:bg-gray-100 transition-all', 'text-black font-sans font-semibold hover:bg-gray-100 transition-all')

content = content.replace('text-xs font-medium text-gray-300', 'font-sans text-body-sm font-medium text-gray-300')
content = content.replace('text-gray-300 text-sm leading-relaxed mb-6 italic', 'font-sans text-body-sm italic text-gray-300 mb-6')

with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
