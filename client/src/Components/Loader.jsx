import React, { useEffect, useState } from 'react'

const Loader = () => {
  const [dots, setDots] = useState('.');
  const [timeLeft, setTimeLeft] = useState(120);
  const [loadingPhase, setLoadingPhase] = useState(0);

  const loadingMessages = [
    "Scraping data from multiple platforms...",
    "Analyzing competitor strategies...",
    "Identifying user pain points and triggers...",
    "Extracting high-performing content patterns...",
    "Generating actionable marketing insights...",
    "Preparing comprehensive analysis..."
  ];

  const analysisSteps = [
    {
      title: "Data Collection",
      steps: [
        "Gathering YouTube video metrics",
        "Scanning Reddit discussions",
        "Analyzing Quora insights",
        "Processing social media trends"
      ]
    },
    {
      title: "Content Analysis",
      steps: [
        "Identifying successful hooks",
        "Analyzing CTAs and triggers",
        "Evaluating content formats",
        "Measuring engagement patterns"
      ]
    },
    {
      title: "Market Research",
      steps: [
        "Mapping competitor strategies",
        "Extracting user pain points",
        "Analyzing market sentiment",
        "Identifying growth opportunities"
      ]
    }
  ];

  useEffect(() => {
    const phaseInterval = setInterval(() => {
      setLoadingPhase(prev => (prev + 1) % loadingMessages.length);
    }, 3000);

    const dotsInterval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '.' : prev + '.');
    }, 500);

    const timerInterval = setInterval(() => {
      setTimeLeft(prev => prev > 0 ? prev - 1 : 0);
    }, 1000);

    return () => {
      clearInterval(dotsInterval);
      clearInterval(timerInterval);
      clearInterval(phaseInterval);
    };
  }, []);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className='flex justify-center w-full fixed top-0 left-0 bg-zinc-900/90 z-50 items-center min-h-screen'>
      <div className='w-[90%] max-w-3xl min-h-[70vh] bg-zinc-800 rounded-xl relative p-8 shadow-lg'>
        <div className='space-y-8'>
          {/* Header */}
          <div>
            <h2 className='text-3xl text-white font-bold'>ART Finder Analysis</h2>
            <p className='text-blue-400 text-lg mt-2'>{loadingMessages[loadingPhase]}{dots}</p>
          </div>

          {/* Analysis Progress */}
          <div className='grid grid-cols-1 md:grid-cols-3 gap-6'>
            {analysisSteps.map((section, index) => (
              <div key={index} className='space-y-3'>
                <h3 className='text-white font-medium flex items-center gap-2'>
                  <div className='w-2 h-2 rounded-full bg-blue-400'></div>
                  {section.title}
                </h3>
                <div className='space-y-2 pl-4'>
                  {section.steps.map((step, stepIndex) => (
                    <div key={stepIndex} className='flex items-center gap-2 text-sm'>
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        loadingPhase >= index ? 'bg-emerald-400' : 'bg-zinc-600'
                      }`}></div>
                      <span className={`${
                        loadingPhase >= index ? 'text-zinc-300' : 'text-zinc-500'
                      }`}>
                        {step}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Features Being Analyzed */}
          <div className='bg-zinc-700/30 rounded-lg p-4'>
            <h3 className='text-white font-medium mb-3'>Analyzing Key Features</h3>
            <div className='grid grid-cols-2 md:grid-cols-4 gap-4 text-sm'>
              <div className='space-y-1'>
                <div className='text-emerald-400'>Content Patterns</div>
                <div className='text-zinc-400'>Identifying successful formats</div>
              </div>
              <div className='space-y-1'>
                <div className='text-emerald-400'>User Triggers</div>
                <div className='text-zinc-400'>Mapping emotional responses</div>
              </div>
              <div className='space-y-1'>
                <div className='text-emerald-400'>Market Trends</div>
                <div className='text-zinc-400'>Analyzing growth opportunities</div>
              </div>
              <div className='space-y-1'>
                <div className='text-emerald-400'>Engagement Metrics</div>
                <div className='text-zinc-400'>Measuring performance</div>
              </div>
            </div>
          </div>
        </div>

        {/* Loading indicator */}
        <div className='absolute bottom-6 right-6 text-white'>
          <div className='flex items-center gap-3 bg-zinc-900/50 px-4 py-2 rounded-full text-sm'>
            <div className='w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin'></div>
            <span className='text-zinc-400'>Analyzing</span>
            <span className='text-blue-400'>{formatTime(timeLeft)}</span>
          </div>
        </div>

        {/* Time badge */}
        <div className='absolute top-6 right-6 text-xs text-zinc-400'>
          Est. time: 2 min
        </div>
      </div>
    </div>
  )
}

export default Loader