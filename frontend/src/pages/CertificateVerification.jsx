import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { challengesApi } from "../services/challengesApi";
import CertificateTemplate from "../components/CertificateTemplate";
import { CertificateVerifySkeleton } from "../bones/PageSkeletons";

const CertificateVerification = () => {
  const { certificateId } = useParams();
  const navigate = useNavigate();
  const [certificate, setCertificate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const verifyCertificate = async () => {
      try {
        const data = await challengesApi.verifyCertificate(certificateId);
        setCertificate(data);
      } catch {
        setError("Certificate not found or invalid");
      } finally {
        setLoading(false);
      }
    };

    verifyCertificate();
  }, [certificateId]);

  if (loading) {
    return <CertificateVerifySkeleton />;
  }

  if (error || !certificate?.valid) {
    return (
      <div className="h-screen flex items-center justify-center bg-zinc-950 px-4 overflow-hidden">
        <div className="max-w-md w-full bg-zinc-900 border border-white/5 rounded-2xl shadow-2xl p-6 text-center">
          <div className="w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4 text-red-500">
            <svg
              className="w-6 h-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2 tracking-tight">
            Access Denied
          </h2>
          <p className="text-zinc-400 mb-6 text-xs leading-relaxed">
            {error || "This certificate could not be verified."}
          </p>
          <button
            onClick={() => navigate("/")}
            className="w-full py-2.5 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-xl transition-all font-semibold text-sm"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const certData = certificate.certificate || certificate;
  const studentName = certData.username || "Student Name";
  const dateObj = new Date(
    certData.created_at || certData.issued_date || Date.now(),
  );
  const formattedDate = dateObj.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  const verifyUrl =
    certData.verification_url ||
    `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/verify/${certificateId}`;

  return (
    <div className="h-screen w-screen bg-zinc-950 text-zinc-200 selection:bg-primary/30 selection:text-primary-foreground relative overflow-hidden flex flex-col p-2 md:p-4 lg:p-6">
      {/* Background Decor */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[100px] animate-pulse" />
        <div
          className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-orange-600/5 rounded-full blur-[100px] animate-pulse"
          style={{ animationDelay: "2s" }}
        />
      </div>

      <div className="flex-1 flex flex-col max-w-6xl mx-auto w-full gap-3 relative z-10 overflow-hidden px-2">
        {/* Compact Header */}
        <header className="flex items-center justify-between gap-3 bg-zinc-900/50 backdrop-blur-xl border border-white/5 p-3 rounded-xl shadow-lg shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">
                Credential Verified
              </h1>
              <p className="text-zinc-500 text-[10px]">
                Verified via CLASHCODE Network
              </p>
            </div>
          </div>
          <div className="hidden sm:block">
            <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-bold uppercase tracking-widest">
              Status: Valid
            </div>
          </div>
        </header>

        {/* Compressed Main Content Area */}
        <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 overflow-hidden min-h-0">
          {/* Certificate Viewport */}
          <div className="lg:col-span-8 group relative bg-zinc-900/20 backdrop-blur-md border border-white/5 rounded-xl shadow-xl overflow-hidden flex items-center justify-center p-2">
            <div className="w-full h-full flex items-center justify-center relative overflow-hidden">
              <div className="origin-center scale-[0.22] sm:scale-[0.35] md:scale-[0.42] lg:scale-[0.5] xl:scale-[0.58] transform-gpu transition-all duration-500 ease-out">
                <CertificateTemplate
                  studentName={studentName}
                  completionDate={formattedDate}
                  verificationUrl={verifyUrl}
                />
              </div>
            </div>

            <button
              onClick={() => window.open(verifyUrl, "_blank")}
              className="absolute top-3 right-3 p-2 rounded-lg bg-zinc-900/80 border border-white/10 text-white hover:bg-zinc-800 transition-all opacity-0 lg:group-hover:opacity-100"
              title="Full Size"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </button>
          </div>

          {/* Compressed Sidebar */}
          <aside className="lg:col-span-4 flex flex-col gap-3 overflow-hidden min-h-0">
            <div className="bg-zinc-900/40 backdrop-blur-xl border border-white/5 p-4 rounded-xl shadow-lg flex flex-col gap-4">
              <div className="space-y-3">
                <h3 className="text-zinc-500 text-[8px] font-bold uppercase tracking-[0.2em]">
                  Identity Details
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3">
                  <section>
                    <span className="block text-[8px] text-zinc-600 uppercase font-medium">
                      Holder
                    </span>
                    <span className="text-sm text-white font-bold">
                      {studentName}
                    </span>
                  </section>
                  <section>
                    <span className="block text-[8px] text-zinc-600 uppercase font-medium">
                      Learning Path
                    </span>
                    <span className="text-xs text-zinc-200 font-semibold truncate block">
                      Python Mastery Course
                    </span>
                  </section>
                  <section>
                    <span className="block text-[8px] text-zinc-600 uppercase font-medium">
                      Issue Date
                    </span>
                    <span className="text-xs text-zinc-200 font-semibold">
                      {formattedDate}
                    </span>
                  </section>
                </div>

                <div className="h-px bg-white/5" />

                <section>
                  <span className="block text-[8px] text-zinc-600 uppercase font-medium mb-1">
                    Asset ID
                  </span>
                  <div className="text-[9px] text-zinc-400 font-mono bg-black/40 p-2 rounded-lg border border-white/5 truncate">
                    {certificateId}
                  </div>
                </section>
              </div>

              <div className="flex flex-col gap-2 pt-1 border-t border-white/5">
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(window.location.href);
                      alert("Copied!");
                    }}
                    className="py-2.5 bg-zinc-800/60 hover:bg-zinc-700 text-white text-[10px] font-bold rounded-lg transition-all border border-white/10"
                  >
                    Copy Link
                  </button>
                  <button
                    onClick={() => navigate("/")}
                    className="py-2.5 bg-zinc-800/20 hover:bg-zinc-800 text-zinc-400 hover:text-white text-[10px] font-bold rounded-lg transition-all border border-white/5"
                  >
                    Back
                  </button>
                </div>
              </div>
            </div>

            {/* Expanded Proof Badge */}
            <div className="hidden sm:flex flex-1 bg-emerald-500/[0.03] border border-emerald-500/10 p-4 rounded-xl items-center justify-center text-center gap-3 shadow-inner">
              <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 shrink-0 shadow-lg">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <p className="text-sm text-emerald-500/80 font-bold tracking-tight">
                Verified Official Credential
              </p>
            </div>
          </aside>
        </main>

        {/* Global Footer */}
        <footer className="py-2 shrink-0 text-center border-t border-white/5">
          <p className="text-[8px] uppercase tracking-[0.4em] font-extrabold text-zinc-700/60">
            End of Credential Record
          </p>
        </footer>
      </div>

      <style
        dangerouslySetInnerHTML={{
          __html: `
        @media print {
          .z-10, .fixed, footer, header, aside, .absolute, button, style { display: none !important; }
          .h-screen { background: white !important; height: auto !important; padding: 0 !important; display: block !important; overflow: visible !important; }
          .origin-center { transform: scale(1) !important; width: 1000px !important; height: 707px !important; margin: 0 auto !important; position: static !important; }
          body { overflow: visible !important; }
        }
      `,
        }}
      />
    </div>
  );
};

export default CertificateVerification;
