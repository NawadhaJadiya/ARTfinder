import React, { useState, useRef, useEffect } from 'react';
import { ArrowRight, Rocket } from "lucide-react";
import axios from 'axios';
import { useTheme } from '../context/ThemeContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { URL } from '../constant/url';


const LoadingMessage = () => (
    <div className='flex items-start gap-2 hover:bg-zinc-800 rounded p-2'>
        <img
            src="/logo.png"
            alt="ai"
            className='w-8 h-8 rounded border border-zinc-600 flex-shrink-0'
        />
        <div className='flex-1 min-w-0'>
            <div className='flex items-center gap-2'>
                <p className='text-sm font-medium bg-green-500 text-transparent bg-clip-text'>
                    ARTfinder Ai
                </p>
            </div>
            <div className='mt-1 bg-transparent rounded-md p-2'>
                <div className='animate-pulse flex'>
                    <span className='text-zinc-400 text-sm'>Response generating...</span>
                </div>
            </div>
        </div>
    </div>
);

const MessageContent = ({ content, theme }) => {
    return (
        <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
                h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2" {...props} />,
                h4: ({node, ...props}) => <h4 className="text-md font-semibold mt-3 mb-1" {...props} />,
                p: ({node, ...props}) => <p className="mb-2" {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc ml-6 mb-2" {...props} />,
                ol: ({node, ...props}) => <ol className="list-decimal ml-6 mb-2" {...props} />,
                li: ({node, ...props}) => <li className="mb-1" {...props} />,
                strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
            }}
            className={`text-sm ${theme === 'dark' ? 'text-zinc-300' : 'text-black'} break-words`}
        >
            {content}
        </ReactMarkdown>
    );
};

const Chat = () => {
    const [active, setActive] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showDetails, setShowDetails] = useState({});  // Track which messages show details
    const messagesEndRef = useRef(null);
    const { theme } = useTheme();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleChat = async () => {
        if (!inputText.trim()) return;

        const newUserMessage = {
            type: 'user',
            content: inputText,
            avatar: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRlvA7GIu55Y8DhQqsNrhNa6D6XofSNMrdWWKkBklXoezSPPo5K8aj2-iUwQmmu4Tx91ZA&usqp=CAU"
        };

        setMessages(prev => [...prev, newUserMessage]);
        setActive(true);
        setInputText('');
        setIsLoading(true);

        try {
            const aiResponse = await axios.post(`${URL}/chat`, {
                message: inputText
            });

            const newMessageId = Date.now();
            setShowDetails(prev => ({ ...prev, [newMessageId]: false }));

            const newAiMessage = {
                id: newMessageId,
                type: 'ai',
                content: aiResponse.data.response || "No response available",
                insights: aiResponse.data.insights || {},
                references: Array.isArray(aiResponse.data.references) ? aiResponse.data.references : [],
                avatar: "/logo.png"
            };

            setMessages(prev => [...prev, newAiMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage = {
                type: 'ai',
                content: "Sorry, I encountered an error processing your request.",
                avatar: "/logo.png"
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleDetails = (messageId) => {
        setShowDetails(prev => ({
            ...prev,
            [messageId]: !prev[messageId]
        }));
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleChat();
        }
    };

    return (
        <div className={`w-[45%] ${theme === 'dark' ? 'bg-[#121212]' : 'bg-white'} h-full flex flex-col`}>
            <div className='flex-1 p-2 overflow-y-auto'>
                {active && messages.length > 0 ? (
                    <div className="space-y-3">
                        {messages.map((message) => (
                            <div key={message.id || Math.random()} className={`flex items-start gap-2 ${theme === 'dark' ? 'hover:bg-zinc-800' : 'hover:bg-zinc-300'} rounded p-2`}>
                                <img
                                    src={message.avatar}
                                    alt={message.type}
                                    className='w-8 h-8 rounded border border-zinc-600 flex-shrink-0'
                                />
                                <div className='flex-1 min-w-0'>
                                    <div className='flex items-center gap-2'>
                                        {message.type === 'user' ? (
                                            <p className={`text-sm ${theme === 'dark' ? 'text-purple-400' : 'text-purple-800'} font-medium`}>User</p>
                                        ) : (
                                            <p className={`text-sm ${theme === 'dark' ? 'text-green-400' : 'text-green-800'} font-medium`}>
                                                ARTfinder Ai
                                            </p>
                                        )}
                                    </div>
                                    <div className={`mt-1 ${message.type === 'ai' ? 'bg-zinc-500/30' : ''} rounded-md p-2`}>
                                        {message.type === 'ai' ? (
                                            <>
                                                <MessageContent content={message.content} theme={theme} />
                                                
                                                {(message.insights && Object.keys(message.insights).length > 0) || 
                                                 (message.references && message.references.length > 0) ? (
                                                    <button
                                                        onClick={() => toggleDetails(message.id)}
                                                        className={`mt-2 text-xs ${theme === 'dark' ? 'text-zinc-400' : 'text-gray-600'} hover:underline`}
                                                    >
                                                        {showDetails[message.id] ? 'Hide Details' : 'Show Details'}
                                                    </button>
                                                ) : null}

                                                {showDetails[message.id] && (
                                                    <div className="mt-4 space-y-4">
                                                        {message.insights && Object.keys(message.insights).length > 0 && (
                                                            <div className="border-t border-zinc-600 pt-4">
                                                                <h4 className={`text-sm font-semibold mb-2 ${theme === 'dark' ? 'text-zinc-300' : 'text-black'}`}>
                                                                    Detailed Insights:
                                                                </h4>
                                                                <div className="space-y-2">
                                                                    {Object.entries(message.insights).map(([key, value]) => (
                                                                        <div key={key} className="text-sm">
                                                                            <strong className={theme === 'dark' ? 'text-zinc-400' : 'text-gray-700'}>
                                                                                {key.replace(/_/g, ' ').toUpperCase()}:
                                                                            </strong>
                                                                            <pre className={`mt-1 whitespace-pre-wrap ${theme === 'dark' ? 'text-zinc-300' : 'text-black'}`}>
                                                                                {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
                                                                            </pre>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {message.references && message.references.length > 0 && (
                                                            <div className="border-t border-zinc-600 pt-4">
                                                                <h4 className={`text-sm font-semibold mb-2 ${theme === 'dark' ? 'text-zinc-300' : 'text-black'}`}>
                                                                    References:
                                                                </h4>
                                                                <ul className="list-disc pl-4">
                                                                    {message.references.map((ref, idx) => (
                                                                        <li key={idx} className={`text-sm ${theme === 'dark' ? 'text-zinc-300' : 'text-black'}`}>
                                                                            {typeof ref === 'object' ? JSON.stringify(ref) : ref}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </>
                                        ) : (
                                            <p className={`text-sm ${theme === 'dark' ? 'text-zinc-400' : 'text-black'} break-words`}>
                                                {message.content}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {isLoading && <LoadingMessage />}
                        <div ref={messagesEndRef} />
                    </div>
                ) : (
                    <div className='flex flex-col items-center justify-center h-full'>
                        <Rocket size={50} className={`${theme === 'dark' ? 'text-white' : 'text-black'}`} />
                        <h1 className={`text-xl font-semibold mt-2 ${theme === 'dark' ? 'text-white' : 'text-black'}`}>New Chat</h1>
                        <p className={`text-md ${theme === 'dark' ? 'text-zinc-500' : 'text-gray-500'} mt-1`}>Start the analysing through chat</p>
                    </div>
                )}
            </div>

            <div className={`p-2 ${theme === 'dark' ? 'bg-[#141414] border-zinc-800' : 'bg-gray-200 border-zinc-400'} border-t`}>
                <div className='relative'>
                    <textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyPress={handleKeyPress}
                        className={`w-full h-20 border outline-none p-3 rounded-md text-sm resize-none ${theme === 'dark' ? 'bg-[#0A0A0A] border-zinc-800 text-white' : 'bg-white border-zinc-200 text-gray-900'}`}
                        placeholder='Send a message...'
                        disabled={isLoading}
                    />
                    <button
                        className="absolute bottom-3 right-2"
                        onClick={handleChat}
                        disabled={!inputText.trim() || isLoading}
                    >
                        <ArrowRight
                            className={`${theme === 'dark' ? 'text-black bg-white' : 'text-white bg-black'} p-1 rounded ${isLoading ? 'opacity-50' : ''}`}
                            size={25}
                        />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Chat;