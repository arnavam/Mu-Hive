import React from "react";
import { MapPin, Calendar, ExternalLink, Globe } from "lucide-react";

// Mock Data
const MOCK_DATA = {
  "Web Development": [
    {
      eventName: "HackOut 2026",
      platform: "Devfolio",
      location: "Kochi, Kerala",
      startDate: "12 Apr 2026",
      score: 140,
      registrationLink: "https://devfolio.co",
      is_new: true,
    },
    {
      eventName: "React Native Hack",
      platform: "Devfolio",
      location: "Online",
      startDate: "15 Apr 2026",
      score: 95,
      registrationLink: "https://devfolio.co",
      is_new: false,
    },
  ],
  "Cyber Security": [
    {
      eventName: "DefCamp India",
      platform: "Unstop",
      location: "Online",
      startDate: "20 Apr 2026",
      score: 110,
      registrationLink: "https://unstop.com",
      is_new: false,
    },
  ],
  "AI & ML": [
    {
      eventName: "GenAI Hack",
      platform: "HackerEarth",
      location: "Bangalore, KA",
      startDate: "05 May 2026",
      score: 160,
      registrationLink: "https://hackerearth.com",
      is_new: true,
    },
  ],
  "Empty Category": [],
};

const ScoreBadge = ({ score }) => {
  let colorClass = "bg-gray-500/10 text-gray-400 border-gray-500/20";
  if (score >= 130) {
    colorClass = "bg-green-500/10 text-green-400 border-green-500/20";
  } else if (score >= 100) {
    colorClass = "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
  } else if (score >= 50) {
    colorClass = "bg-blue-500/10 text-blue-400 border-blue-500/20";
  }

  return (
    <div
      className={`px-2.5 py-1 rounded border text-xs font-semibold backdrop-blur-sm ${colorClass}`}
    >
      Score: {score}
    </div>
  );
};

const HackathonCard = ({ event }) => {
  return (
    <div className="relative group bg-gray-900/50 backdrop-blur-md rounded-xl border border-gray-800 p-6 hover:border-indigo-500/50 hover:bg-gray-800/80 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgb(99,102,241,0.15)] flex flex-col h-full">
      {/* Top badges */}
      <div className="flex justify-between items-start mb-4">
        <ScoreBadge score={event.score} />
        {event.is_new && (
          <div className="px-2 py-1 rounded bg-indigo-500/20 text-indigo-400 text-xs font-bold font-mono tracking-wider animate-pulse border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.5)]">
            NEW
          </div>
        )}
      </div>

      {/* Main Info */}
      <div className="mb-6 flex-grow">
        <h3 className="text-xl font-bold text-white mb-3 group-hover:text-indigo-300 transition-colors">
          {event.eventName}
        </h3>
        
        <div className="space-y-2 text-sm text-gray-400">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-gray-500" />
            <span>{event.platform}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span>{event.location}</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span>{event.startDate}</span>
          </div>
        </div>
      </div>

      {/* Action */}
      <a
        href={event.registrationLink}
        target="_blank"
        rel="noopener noreferrer"
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors focus:ring-4 focus:ring-indigo-500/30"
      >
        <span>Apply Now</span>
        <ExternalLink className="w-4 h-4" />
      </a>
    </div>
  );
};

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-100 font-sans selection:bg-indigo-500/30">
      
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Globe className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                SJCET Hackathon Radar
              </h1>
              <p className="text-xs text-indigo-400 font-medium tracking-widest uppercase mt-0.5">
                Curated Opportunities
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
        {Object.entries(MOCK_DATA).map(([groupName, hackathons]) => {
          if (!hackathons || hackathons.length === 0) return null;

          return (
            <section key={groupName} className="relative z-10">
              {/* Added a subtle glow effect behind the section title */}
              <div className="absolute -inset-x-4 -top-8 -bottom-8 bg-gradient-to-b from-gray-800/10 to-transparent -z-10 rounded-[3rem] blur-2xl opacity-50"></div>
              
              <div className="mb-8">
                <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                  <span className="w-2 h-8 bg-indigo-500 rounded-full inline-block"></span>
                  {groupName}
                </h2>
                <p className="text-gray-400 mt-2 ml-5">
                  Top opportunities picked for your interest group
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 ml-5 lg:grid-cols-3 gap-6">
                {hackathons.map((event, idx) => (
                  <HackathonCard key={`${event.eventName}-${idx}`} event={event} />
                ))}
              </div>
            </section>
          );
        })}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 text-center text-gray-500 text-sm">
        <p>© 2026 SJCET Hackathon Radar. Stay sharp.</p>
      </footer>
    </div>
  );
};

export default Dashboard;
