import React, { useState, useRef, useEffect } from 'react';
import Loader from './Components/Loader';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import InstagramProfile from './Components/InstagramProfile';
import { Link } from 'react-router-dom';
// import data from './demo.js';
import Chat from './Components/Chat';
import { URL } from './constant/url';

const Analysis = () => {
  const location = useLocation();
  const [data, setData] = useState(null);
  console.log(data)
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const queryParams = new URLSearchParams(location.search);
  const uname = queryParams.get('uname');
  const dataFetchedRef = useRef(false);

  // Prevent accidental page reload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = '';
      return '';
    };

    // Prevent back button
    const handlePopState = (e) => {
      e.preventDefault();
      if (window.confirm('Are you sure you want to leave? Your analysis progress will be lost.')) {
        navigate('/');
      } else {
        window.history.pushState(null, null, window.location.pathname);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopState);
    
    // Push a new entry to prevent immediate back
    window.history.pushState(null, null, window.location.pathname);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [navigate]);

  // Account related Code - Only fetch once
  useEffect(() => {
    const postData = async () => {
      if (dataFetchedRef.current) return;
      setIsLoading(true);
      try {
        const response = await axios.post(`${URL}/analyze`, {
          message: uname,
        });
        setData(response.data);
        dataFetchedRef.current = true;
      } catch (err) {
        setError(err);
        console.log(err);
      } finally {
        setIsLoading(false);
      }
    };

    if (uname && !dataFetchedRef.current) {
      postData();
    }
  }, [uname]);

  // console.log(data)

  // Prevent accidental page reload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = '';
      return '';
    };

    // Prevent back button
    const handlePopState = (e) => {
      e.preventDefault();
      if (window.confirm('Are you sure you want to leave? Your analysis progress will be lost.')) {
        navigate('/');
      } else {
        window.history.pushState(null, null, window.location.pathname);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopState);
    
    // Push a new entry to prevent immediate back
    window.history.pushState(null, null, window.location.pathname);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [navigate]);

  return (
    <>
      {isLoading && <Loader />}
      <div className='flex h-screen text-white'>
        {/* Left Area */}
        <div className='w-[55%] overflow-y-auto h-full no-scrollbar'>
          {/* Background gradients */}
          <div className="fixed top-0 left-0 right-0 pointer-events-none">
            <div className="absolute top-[-40vh] left-[5vh] z-[-1]">
              <div className="w-[40vw] h-[30vh] bg-purple-400 blur-[8rem] rounded-full opacity-20"></div>
              <div className="w-[20vw] h-[40vh] bg-purple-900 blur-[10rem] rounded-full opacity-20"></div>
            </div>
          </div>
          
          {/* Header */}
          <div className='sticky top-0 z-10 py-2 px-4 backdrop-blur-sm'>
            <Link to="/" className="logo font-bold italic text-[1.2rem] text-white">
              ARTfinder
            </Link>
          </div>

          {/* Main Content */}
          <div className="relative z-0">
            {error && (
              <div className="p-6 text-center text-red-400">
                Error loading analysis: {error.message}
              </div>
            )}
            {data && Object.keys(data).length > 0 && <InstagramProfile data={data} />}
          </div>
        </div>

        {/* Right Area */}
        <Chat />
      </div>
    </>
  );
};

export default Analysis;