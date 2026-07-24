import Header from "./components/Header";
import AnalyzeForm from "./components/AnalyzeForm";
import api from "./services/api";

function App() {


  const handleAnalyze = async (url) => {
    try {
      const response = await api.post("/analyze", {
        video_url: url,
      });

      console.log(response.data);
    }   catch (error) {
      console.error("API Error:", error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header />

      <AnalyzeForm onAnalyze={handleAnalyze} />
    </div>
  );
}

export default App;