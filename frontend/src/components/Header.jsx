function Header() {
  return (
    <header className="flex items-center justify-between px-8 py-6 border-b border-slate-800">
      <div>
        <h1 className="text-3xl font-bold text-cyan-400">
          🛡 TruthLens
        </h1>

        <p className="text-slate-400 text-sm mt-1">
          AI-powered Video Fact Checker
        </p>
      </div>

      <div className="text-sm text-slate-500">
        Powered by Langraph
        
      </div>
    </header>
  );
}

export default Header;