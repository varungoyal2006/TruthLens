import { useState } from "react";

function AnalyzeForm({ onAnalyze }) {
  const [videoUrl, setVideoUrl] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!videoUrl.trim()) return;

    onAnalyze(videoUrl);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-2xl mx-auto mt-20 bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-800"
    >
      <h2 className="text-3xl font-bold text-white text-center">
        Analyze a YouTube Video
      </h2>

      <p className="text-slate-400 text-center mt-2">
        Verify factual accuracy using AI, Hybrid RAG and trusted sources.
      </p>

      <input
        type="url"
        placeholder="Paste YouTube video URL..."
        value={videoUrl}
        onChange={(e) => setVideoUrl(e.target.value)}
        className="w-full mt-8 p-4 rounded-xl bg-slate-800 border border-slate-700 text-white outline-none focus:border-cyan-400"
      />

      <button
        type="submit"
        className="w-full mt-6 bg-cyan-500 hover:bg-cyan-600 transition rounded-xl py-4 font-semibold text-slate-950"
      >
        Analyze Video
      </button>
    </form>
  );
}

export default AnalyzeForm;