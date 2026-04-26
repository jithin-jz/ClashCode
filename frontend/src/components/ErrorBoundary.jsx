import React from "react";
import { AlertTriangle, RefreshCw, Home, ChevronRight } from "lucide-react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  render() {
    const isDev = import.meta.env.DEV;

    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#050505] font-sans selection:bg-red-500/30">
          {/* Subtle Background Glows */}
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-red-500/10 blur-[120px] rounded-full pointer-events-none" />
          
          <div className="relative z-10 max-w-xl w-full mx-6">
            <div className="bg-[#0A0A0A]/80 backdrop-blur-2xl border border-white/5 rounded-3xl p-8 sm:p-10 shadow-2xl shadow-black">
              {/* Animated Icon */}
              <div className="flex items-center justify-center w-20 h-20 mx-auto mb-8 relative">
                <div className="absolute inset-0 bg-red-500/20 blur-2xl rounded-full animate-pulse" />
                <div className="relative flex items-center justify-center w-full h-full bg-red-500/10 border border-red-500/20 rounded-2xl">
                  <AlertTriangle size={36} className="text-red-500" />
                </div>
              </div>

              <div className="text-center space-y-3 mb-10">
                <h1 className="text-3xl font-bold text-white tracking-tight">
                  System Interruption
                </h1>
                <p className="text-neutral-400 text-sm leading-relaxed max-w-xs mx-auto">
                  A runtime exception was detected. Our automated protocols have isolated the issue.
                </p>
              </div>

              {isDev && this.state.error && (
                <div className="mb-8 rounded-2xl border border-white/5 bg-black/40 overflow-hidden">
                  <details className="group">
                    <summary className="flex items-center justify-between cursor-pointer p-4 text-xs font-bold text-red-400/80 uppercase tracking-widest hover:bg-white/[0.02] transition-colors">
                      <span className="flex items-center gap-2">
                        <ChevronRight size={14} className="group-open:rotate-90 transition-transform" />
                        Diagnostic Data (Dev Mode)
                      </span>
                    </summary>
                    <div className="px-4 pb-4 mt-1">
                      <pre className="text-[10px] font-mono text-neutral-500 overflow-auto max-h-48 ds-scrollbar leading-relaxed">
                        <span className="text-red-400/60 font-bold block mb-2">{this.state.error.toString()}</span>
                        {this.state.errorInfo && this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  </details>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button
                  onClick={() => (window.location.href = "/")}
                  className="group flex items-center justify-center gap-2 bg-white text-black font-bold py-3.5 px-6 rounded-2xl transition-all hover:bg-neutral-200 active:scale-95"
                >
                  <Home size={18} />
                  <span>Go Home</span>
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="group flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-white font-bold py-3.5 px-6 rounded-2xl transition-all hover:bg-white/10 active:scale-95"
                >
                  <RefreshCw size={18} className="group-hover:rotate-180 transition-transform duration-500" />
                  <span>Reload Session</span>
                </button>
              </div>

              <div className="mt-8 text-center">
                <p className="text-[10px] text-neutral-600 uppercase tracking-[0.2em] font-medium">
                  Protocol: Error_Recovery_v4.2
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
