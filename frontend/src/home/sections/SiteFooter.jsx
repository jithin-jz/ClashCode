import React from "react";
import { Github, Linkedin, Twitter, Youtube } from "lucide-react";

const socialLinks = [
  { label: "GitHub", href: "https://github.com/jithin-jz", Icon: Github },
  { label: "LinkedIn", href: "https://www.linkedin.com/in/jithin-kr/", Icon: Linkedin },
  { label: "Twitter", href: "https://x.com/jithin_jz", Icon: Twitter },
  { label: "YouTube", href: "https://www.youtube.com/@jithinjz", Icon: Youtube },
];

const SiteFooter = () => {
  const year = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-neutral-900 bg-black">
      <div className="max-w-[1200px] mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
        {/* Left */}
        <div className="flex items-center gap-4">
          <span className="text-[11px] font-medium text-neutral-500">
            CLASHCODE
          </span>
          <span className="text-[11px] text-neutral-700">© {year}</span>
        </div>

        {/* Right: Socials */}
        <div className="flex items-center gap-3">
          {socialLinks.map((s) => (
            <a
              key={s.label}
              href={s.href}
              target="_blank"
              rel="noreferrer"
              className="text-neutral-700 hover:text-neutral-400 transition-colors"
              aria-label={s.label}
            >
              {React.createElement(s.Icon, { size: 14, strokeWidth: 1.5 })}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
};

export default SiteFooter;
