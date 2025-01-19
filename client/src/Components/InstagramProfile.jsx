import React, { useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  CartesianGrid,
  Legend,
  PieChart,
  Pie,
  Cell,
  ReferenceLine,
  ScatterChart,
  Scatter
} from "recharts";
import { 
  ChevronDown, ChevronUp, Activity, TrendingUp, 
  Target, Lightbulb, Users, ShoppingBag, Zap, Globe, TrendingDown, BarChart2, Layout
} from "lucide-react";

// Custom styles for markdown content
const markdownStyles = {
  h1: "text-2xl font-bold text-white mb-4",
  h2: "text-xl font-bold text-white mt-6 mb-3",
  h3: "text-lg font-semibold text-white mt-4 mb-2",
  p: "text-zinc-300 mb-4",
  ul: "list-disc pl-6 mb-4 space-y-2",
  li: "text-zinc-300",
  strong: "text-white font-semibold",
  em: "text-zinc-400 italic",
};

const CustomMarkdown = ({ content }) => {
  // Add check for content type and convert to string if needed
  const markdownContent = typeof content === 'string' ? content : JSON.stringify(content);
  
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({node, ...props}) => <h1 className={markdownStyles.h1} {...props} />,
        h2: ({node, ...props}) => <h2 className={markdownStyles.h2} {...props} />,
        h3: ({node, ...props}) => <h3 className={markdownStyles.h3} {...props} />,
        p: ({node, ...props}) => <p className={markdownStyles.p} {...props} />,
        ul: ({node, ...props}) => <ul className={markdownStyles.ul} {...props} />,
        li: ({node, ...props}) => <li className={markdownStyles.li} {...props} />,
        strong: ({node, ...props}) => <strong className={markdownStyles.strong} {...props} />,
        em: ({node, ...props}) => <em className={markdownStyles.em} {...props} />,
      }}
    >
      {markdownContent}
    </ReactMarkdown>
  );
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-800 border border-zinc-700 p-2 rounded-lg shadow-lg">
        <p className="text-zinc-300 text-xs font-medium">{`Date: ${label}`}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs" style={{ color: entry.color }}>
            {`${entry.name}: ${entry.value}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Update the calculateGrowthData function for more systematic calculations
const calculateGrowthData = (trendData) => {
  if (!trendData.length) return [];
  
  const monthlyData = [];
  const monthlyTotals = {};
  
  // First, group data by month
  trendData.forEach(item => {
    const date = new Date(item.date);
    const monthKey = `${date.getFullYear()}-${date.getMonth() + 1}`;
    
    if (!monthlyTotals[monthKey]) {
      monthlyTotals[monthKey] = {
        total: 0,
        count: 0,
        month: date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
      };
    }
    
    // Sum all numeric values for this data point
    const dayTotal = Object.entries(item).reduce((sum, [key, value]) => {
      return key !== 'date' && !isNaN(value) ? sum + value : sum;
    }, 0);
    
    monthlyTotals[monthKey].total += dayTotal;
    monthlyTotals[monthKey].count += 1;
  });
  
  // Calculate growth rates
  let previousValue = null;
  Object.keys(monthlyTotals).sort().forEach(monthKey => {
    const avgValue = monthlyTotals[monthKey].total / monthlyTotals[monthKey].count;
    
    if (previousValue !== null) {
      const growthRate = ((avgValue - previousValue) / previousValue) * 100;
      monthlyData.push({
        month: monthlyTotals[monthKey].month,
        growth: parseFloat(growthRate.toFixed(1)),
        avgValue: Math.round(avgValue)
      });
    }
    previousValue = avgValue;
  });
  
  return monthlyData;
};

// Add this new component for implementation guide
const ImplementationGuide = ({ data }) => (
  <div className="space-y-6">
    {/* Content Strategy */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
        <h3 className="text-sm font-medium text-white mb-3">Content Strategy</h3>
        <div className="space-y-4">
          {[
            { platform: "Instagram", types: ["Reels", "Stories", "Posts"], frequency: "2-3x daily" },
            { platform: "TikTok", types: ["Short-form", "Trends", "UGC"], frequency: "1-2x daily" },
            { platform: "YouTube", types: ["Long-form", "Shorts"], frequency: "2x weekly" }
          ].map((platform, index) => (
            <div key={index} className="border-b border-zinc-700/50 pb-3 last:border-0 last:pb-0">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-white">{platform.platform}</span>
                <span className="text-xs text-zinc-400">{platform.frequency}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {platform.types.map((type, i) => (
                  <span key={i} className="px-2 py-1 rounded-full bg-zinc-700/50 text-xs text-zinc-300">
                    {type}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
        <h3 className="text-sm font-medium text-white mb-3">Campaign Framework</h3>
        <div className="space-y-3">
          {[
            { type: "Awareness", elements: ["Brand Story", "Value Proposition", "Social Proof"] },
            { type: "Consideration", elements: ["Product Features", "Comparisons", "Reviews"] },
            { type: "Conversion", elements: ["Offers", "Limited Time", "Call-to-Action"] }
          ].map((phase, index) => (
            <div key={index} className="space-y-2">
              <h4 className="text-xs font-medium text-zinc-400">{phase.type}</h4>
              <div className="flex flex-wrap gap-2">
                {phase.elements.map((element, i) => (
                  <span key={i} className="px-2 py-1 rounded-full bg-zinc-700/50 text-xs text-zinc-300">
                    {element}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>

    {/* Visual Guidelines */}
    <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
      <h3 className="text-sm font-medium text-white mb-4">Visual Guidelines</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <h4 className="text-xs font-medium text-zinc-400 mb-3">Brand Colors</h4>
          <div className="flex gap-2">
            {['#4ade80', '#2563eb', '#f59e0b'].map((color, index) => (
              <div key={index} className="flex flex-col items-center">
                <div 
                  className="w-8 h-8 rounded-full mb-1"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs text-zinc-500">{color}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-medium text-zinc-400 mb-3">Typography</h4>
          <div className="space-y-2">
            <div className="text-sm text-zinc-300">Headings: Inter Bold</div>
            <div className="text-sm text-zinc-300">Body: Inter Regular</div>
            <div className="text-sm text-zinc-300">Accents: Inter Medium</div>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-medium text-zinc-400 mb-3">Image Style</h4>
          <div className="space-y-2">
            <div className="text-sm text-zinc-300">Lifestyle Photography</div>
            <div className="text-sm text-zinc-300">Brand-colored Overlays</div>
            <div className="text-sm text-zinc-300">Consistent Filters</div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Add a new component to display pain points and triggers
const InsightsList = ({ data }) => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
            <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                <Target className="w-4 h-4 text-purple-400" />
                Pain Points
            </h3>
            <ul className="space-y-2">
                {data?.metadata?.pain_points?.map((point, index) => (
                    <li key={index} className="text-sm text-zinc-300 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-400/50"></span>
                        {point}
                    </li>
                ))}
            </ul>
        </div>
        <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
            <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                Triggers
            </h3>
            <ul className="space-y-2">
                {data?.metadata?.triggers?.map((trigger, index) => (
                    <li key={index} className="text-sm text-zinc-300 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-yellow-400/50"></span>
                        {trigger}
                    </li>
                ))}
            </ul>
        </div>
    </div>
);

// First, define all helper functions
const calculateTotalSearchVolume = (data) => {
  if (!data?.length) return 0;
  const lastMonth = data.slice(-30);
  const total = lastMonth.reduce((sum, item) => 
    sum + Object.values(item).reduce((a, b) => typeof b === 'number' ? a + b : a, 0), 0
  );
  return Math.round(total / 30);
};

const calculateBrandMentions = (data) => {
  if (!data?.length) return 0;
  const lastMonth = data.slice(-30);
  return Math.round(lastMonth.reduce((sum, item) => sum + (item.brand || 0), 0) / 30);
};

const calculateGrowthRate = (data) => {
  if (!data?.length || data.length < 2) return 0;
  const firstMonth = data.slice(0, 30);
  const lastMonth = data.slice(-30);
  const firstAvg = firstMonth.reduce((sum, item) => sum + (item.trend || 0), 0) / 30;
  const lastAvg = lastMonth.reduce((sum, item) => sum + (item.trend || 0), 0) / 30;
  return Math.round(((lastAvg - firstAvg) / firstAvg) * 100);
};

const TrendSection = ({ data, keywords }) => (
  <div className="space-y-6">
    {/* Enhanced Line Chart */}
    <div className="p-4 rounded-xl border bg-zinc-800/50 border-zinc-700/50">
      <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
        <Activity className="w-4 h-4 text-blue-400" />
        Search Interest Trends
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="date" 
              stroke="#888888" 
              fontSize={12}
              tickFormatter={(value) => new Date(value).toLocaleDateString()}
            />
            <YAxis stroke="#888888" fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {keywords.map((keyword, index) => (
              <Line 
                key={keyword}
                type="monotone" 
                dataKey={keyword} 
                name={keyword}
                stroke={`hsl(${index * 60}, 70%, 50%)`}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>

    {/* Growth Rate Chart */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
        <h3 className="text-sm font-medium text-white mb-4">Growth Rate</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={calculateGrowthData(data)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="month" stroke="#888888" fontSize={12} />
              <YAxis stroke="#888888" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="growth" fill="#4ade80">
                {calculateGrowthData(data).map((entry, index) => (
                  <Cell 
                    key={index} 
                    fill={entry.growth >= 0 ? '#4ade80' : '#f87171'} 
                  />
                ))}
              </Bar>
              <ReferenceLine y={0} stroke="#666" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
        <h3 className="text-sm font-medium text-white mb-4">Sentiment Distribution</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={[
                  { name: 'Positive', value: 35 },
                  { name: 'Neutral', value: 45 },
                  { name: 'Negative', value: 20 }
                ]}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                fill="#8884d8"
                paddingAngle={5}
                dataKey="value"
              >
                {['#4ade80', '#facc15', '#f87171'].map((color, index) => (
                  <Cell key={`cell-${index}`} fill={color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  </div>
);

// Add MarketOverview component
const MarketOverview = ({ data }) => (
  <div className="space-y-6">
    {/* Market Stats */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
        <h3 className="text-sm font-medium text-white mb-3">Market Performance</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-zinc-400">Market Size</span>
            <span className="text-sm text-white font-medium">$12.5B</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-zinc-400">Growth Rate</span>
            <span className="text-sm text-emerald-400">+15.3%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-zinc-400">Market Share</span>
            <span className="text-sm text-white">23.5%</span>
          </div>
        </div>
      </div>
      
      <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
        <h3 className="text-sm font-medium text-white mb-3">Key Demographics</h3>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-400"></span>
            <span className="text-sm text-zinc-300">Age: 25-34 (45%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-purple-400"></span>
            <span className="text-sm text-zinc-300">Urban Areas (65%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="text-sm text-zinc-300">Tech-Savvy (78%)</span>
          </div>
        </div>
      </div>
    </div>

    {/* Trend Analysis */}
    <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
      <h3 className="text-sm font-medium text-white mb-3">Market Trends</h3>
      <div className="space-y-3">
        {[
          { trend: "Digital Transformation", growth: "+28%", status: "Growing" },
          { trend: "Sustainability Focus", growth: "+45%", status: "Rapid Growth" },
          { trend: "Mobile-First", growth: "+32%", status: "Steady" }
        ].map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-zinc-300">{item.trend}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-emerald-400">{item.growth}</span>
              <span className="text-xs text-zinc-500">{item.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// Enhanced CompetitorAnalysis component
const CompetitorAnalysis = ({ data }) => (
  <div className="space-y-6">
    {/* Competitor Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {data?.map((competitor, index) => (
        <div key={index} className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
          <div className="flex justify-between items-start mb-3">
            <h3 className="text-sm font-medium text-white">{competitor.title}</h3>
            <span className={`px-2 py-1 rounded-full text-xs ${
              competitor.sentiment > 0.3 ? 'bg-green-400/10 text-green-400' : 
              competitor.sentiment < 0 ? 'bg-red-400/10 text-red-400' : 
              'bg-yellow-400/10 text-yellow-400'
            }`}>
              {(competitor.sentiment * 100).toFixed(1)}% Sentiment
            </span>
          </div>
          
          <p className="text-sm text-zinc-400 mb-4">{competitor.summary}</p>
          
          {/* Strengths & Strategy */}
          <div className="space-y-3">
            <div>
              <h4 className="text-xs font-medium text-zinc-500 mb-2">Key Strengths</h4>
              <div className="flex flex-wrap gap-2">
                {competitor.content_strategy.formats.map((format, i) => (
                  <span key={i} className="px-2 py-1 rounded-full bg-zinc-700/50 text-zinc-300 text-xs">
                    {format}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="text-xs font-medium text-zinc-500 mb-2">Content Strategy</h4>
              <div className="flex items-center gap-3">
                <span className="text-xs text-zinc-300">{competitor.content_strategy.frequency}</span>
                <span className="text-xs text-zinc-400">on</span>
                <span className="text-xs text-zinc-300">{competitor.content_strategy.channels}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>

    {/* Market Position Map */}
    <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
      <h3 className="text-sm font-medium text-white mb-4">Market Position Analysis</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis type="number" dataKey="marketShare" name="Market Share" stroke="#888" />
            <YAxis type="number" dataKey="growth" name="Growth" stroke="#888" />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Scatter name="Competitors" data={data.map((c, i) => ({
              name: c.title,
              marketShare: 20 + i * 10,
              growth: 15 + Math.random() * 30
            }))} fill="#8884d8">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  </div>
);

// Then define the component
const InstagramProfile = ({ data }) => {
  const [openSection, setOpenSection] = useState('trends');

  // Add safe access to trend data with proper data structure
  const trendData = data?.trend_analysis?.google_trends?.data || [];
  const keywords = data?.trend_analysis?.google_trends?.keywords || [];
  const marketSentiment = data?.metadata?.market_sentiment || {};
  const aiInsights = data?.ai_insights || '';
  const competitorData = data?.competitor_analysis || [];

  // Define metrics after the helper functions are available
  const metrics = [
    {
      title: "Market Sentiment",
      value: marketSentiment.value || "50%",
      label: marketSentiment.label || "Neutral",
      icon: TrendingUp,
      color: "text-emerald-400",
      bgColor: "bg-emerald-400/10"
    },
    {
      title: "Search Volume",
      value: `${calculateTotalSearchVolume(trendData)}`,
      label: "Monthly Average",
      icon: BarChart2,
      color: "text-blue-400",
      bgColor: "bg-blue-400/10"
    },
    {
      title: "Brand Mentions",
      value: `${calculateBrandMentions(trendData)}`,
      label: "Last 30 Days",
      icon: Globe,
      color: "text-purple-400",
      bgColor: "bg-purple-400/10"
    },
    {
      title: "Growth Rate",
      value: `${calculateGrowthRate(trendData)}%`,
      label: "YoY Change",
      icon: TrendingUp,
      color: "text-green-400",
      bgColor: "bg-green-400/10"
    }
  ];

  // Calculate sentiment distribution for pie chart
  const sentimentData = [
    { name: 'Positive', value: competitorData.filter(c => c.sentiment > 0.2).length },
    { name: 'Neutral', value: competitorData.filter(c => c.sentiment >= -0.2 && c.sentiment <= 0.2).length },
    { name: 'Negative', value: competitorData.filter(c => c.sentiment < -0.2).length }
  ];

  const COLORS = ['#4ade80', '#facc15', '#f87171'];

  // Add new sections for the left sidebar
  const sections = {
    overview: {
      title: "Market Overview",
      emoji: "📊",
      icon: Activity,
      content: <MarketOverview data={data} />,
      description: "High-level market metrics and trends"
    },
    trends: {
      title: "Trend Analysis",
      emoji: "📈",
      icon: TrendingUp,
      content: <TrendSection data={trendData} keywords={keywords} />,
      description: "Detailed trend analysis and insights"
    },
    insights: {
      title: "Strategic Insights",
      emoji: "💡",
      icon: Lightbulb,
      content: (
        <div className="space-y-6">
          <CustomMarkdown content={aiInsights} />
          <InsightsList data={data} />
          <ActionableRecommendations data={data} />
        </div>
      ),
      description: "AI-powered strategic recommendations"
    },
    competitors: {
      title: "Competition Analysis",
      emoji: "🎯",
      icon: Target,
      content: <CompetitorAnalysis data={competitorData} />,
      description: "Competitor strategies and market positioning"
    },
    implementation: {
      title: "Implementation Guide",
      emoji: "⚡",
      icon: Zap,
      content: <ImplementationGuide data={data} />,
      description: "Actionable implementation steps"
    }
  };

  // Add this with other data processing
  const growthData = calculateGrowthData(trendData);

  if (!data) {
    return (
      <div className="p-6 text-center text-zinc-400">
        No analysis data available
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 rounded-xl bg-transparent">
      {/* Enhanced Header */}
      <div className="mb-8 text-center">
        <div className="inline-flex items-center justify-center gap-2 mb-2">
          <span className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-sm font-medium">
            Live Analysis
          </span>
        </div>
        <h1 className="text-3xl font-bold text-white mb-3">
          {data?.query ? `Market Analysis: ${data.query}` : 'Market Analysis Report'}
        </h1>
        <p className="text-zinc-400 text-sm max-w-2xl mx-auto">
          Real-time market insights and competitive analysis powered by AI
        </p>
      </div>

      {/* Enhanced Metrics Dashboard */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {metrics.map((metric, index) => (
          <div key={index} 
               className="p-4 rounded-xl border bg-zinc-800/50 border-zinc-700/50 hover:bg-zinc-700/50 transition-colors duration-200">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${metric.bgColor}`}>
                <metric.icon className={`${metric.color} w-5 h-5`} />
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-400">{metric.title}</p>
                <p className="text-lg font-bold text-white">{metric.value}</p>
                <p className="text-xs text-zinc-500">{metric.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Enhanced Accordion Sections */}
      <div className="space-y-4">
        {Object.entries(sections).map(([key, section]) => (
          <div key={key} className={`border border-zinc-700/50 rounded-xl overflow-hidden transition-all duration-300 ${
            openSection === key ? 'bg-zinc-800/50 shadow-lg' : 'bg-zinc-800/30'
          }`}>
            <button
              onClick={() => setOpenSection(openSection === key ? null : key)}
              className="w-full p-4 flex justify-between items-center text-white hover:bg-zinc-700/30 transition-colors duration-200"
            >
              <div className="flex flex-col items-start gap-1">
                <span className="font-medium flex items-center gap-2">
                  <span className="text-xl">{section.emoji}</span>
                  {section.title}
                </span>
                <span className="text-xs text-zinc-400">{section.description}</span>
              </div>
              <span className={`transform transition-transform duration-200 ${
                openSection === key ? 'rotate-180' : ''
              }`}>
                <ChevronDown size={20} />
              </span>
            </button>
            
            <div className={`transition-all duration-300 ${
              openSection === key ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'
            }`}>
              <div className="p-6 border-t border-zinc-700/50">
                {key === 'insights' ? (
                  sections[key].content
                ) : key === 'implementation' ? (
                  sections[key].content
                ) : key === 'trends' ? (
                  <div className="space-y-6">
                    {/* Enhanced Line Chart */}
                    <div className="p-4 rounded-xl border bg-zinc-800/50 border-zinc-700/50">
                      <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-blue-400" />
                        Search Interest Trends
                      </h3>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                            <XAxis 
                              dataKey="date" 
                              stroke="#888888" 
                              fontSize={12}
                              tickFormatter={(value) => new Date(value).toLocaleDateString()}
                            />
                            <YAxis stroke="#888888" fontSize={12} />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            {keywords.map((keyword, index) => (
                              <Line 
                                key={keyword}
                                type="monotone" 
                                dataKey={keyword} 
                                name={keyword}
                                stroke={`hsl(${index * 60}, 70%, 50%)`}
                                strokeWidth={2}
                                dot={false}
                              />
                            ))}
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Sentiment Distribution Pie Chart */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl border bg-zinc-800/50 border-zinc-700/50">
                        <h3 className="text-sm font-medium text-white mb-4">Sentiment Distribution</h3>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={sentimentData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                              >
                                {sentimentData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index]} />
                                ))}
                              </Pie>
                              <Tooltip />
                              <Legend />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* Market Growth Trend */}
                      <div className="p-4 rounded-xl border bg-zinc-800/50 border-zinc-700/50">
                        <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-green-400" />
                          Market Growth Trend
                        </h3>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={growthData}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                              <XAxis 
                                dataKey="month" 
                                stroke="#888888" 
                                fontSize={12}
                                angle={-45}
                                textAnchor="end"
                                height={60}
                              />
                              <YAxis 
                                stroke="#888888" 
                                fontSize={12}
                                tickFormatter={(value) => `${value}%`}
                                domain={['auto', 'auto']}
                              />
                              <Tooltip 
                                content={({ active, payload, label }) => {
                                  if (active && payload && payload.length) {
                                    const data = payload[0].payload;
                                    return (
                                      <div className="bg-zinc-800 border border-zinc-700 p-3 rounded-lg shadow-lg">
                                        <p className="text-zinc-300 text-xs font-medium mb-1">{label}</p>
                                        <p className={`text-xs font-bold ${data.growth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                          Growth Rate: {data.growth}%
                                        </p>
                                        <p className="text-zinc-400 text-xs mt-1">
                                          Average Value: {data.avgValue}
                                        </p>
                                      </div>
                                    );
                                  }
                                  return null;
                                }}
                              />
                              <Bar 
                                dataKey="growth" 
                                radius={[4, 4, 0, 0]}
                              >
                                {growthData.map((entry, index) => (
                                  <Cell 
                                    key={`cell-${index}`}
                                    fill={entry.growth >= 0 ? '#4ade80' : '#f87171'}
                                    opacity={Math.min(0.5 + Math.abs(entry.growth) / 100, 1)}
                                  />
                                ))}
                              </Bar>
                              <ReferenceLine 
                                y={0} 
                                stroke="#666" 
                                strokeDasharray="3 3"
                              />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="mt-3 flex justify-center gap-4 text-xs">
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 bg-green-400 rounded-sm opacity-70"></div>
                            <span className="text-zinc-400">Positive Growth</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 bg-red-400 rounded-sm opacity-70"></div>
                            <span className="text-zinc-400">Negative Growth</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : key === 'competitors' ? (
                  <div className="space-y-4">
                    {section.content}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Add new components for enhanced visualization
const MarketMetricsCard = ({ title, data, type }) => (
  <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
    <h3 className="text-sm font-medium text-white mb-3">{title}</h3>
    <div className="h-40">
      <ResponsiveContainer width="100%" height="100%">
        {type === 'line' ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="value" stroke="#4ade80" />
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" fill="#4ade80" />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  </div>
);

const CompetitorOverview = ({ data }) => (
  <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
    <h3 className="text-sm font-medium text-white mb-3">Competitor Overview</h3>
    <div className="space-y-3">
      {data.map((competitor, index) => (
        <div key={index} className="flex items-center justify-between">
          <span className="text-sm text-zinc-300">{competitor.title}</span>
          <div className="flex items-center gap-2">
            <span className={`text-xs ${
              competitor.sentiment > 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {(competitor.sentiment * 100).toFixed(1)}%
            </span>
            <div className="w-20 h-2 bg-zinc-700 rounded-full overflow-hidden">
              <div 
                className={`h-full ${
                  competitor.sentiment > 0 ? 'bg-green-400' : 'bg-red-400'
                }`}
                style={{ width: `${Math.abs(competitor.sentiment * 100)}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const ActionableRecommendations = ({ data }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
      <h3 className="text-sm font-medium text-white mb-3">Quick Actions</h3>
      <ul className="space-y-2">
        {data?.content_recommendations?.ctas.map((cta, index) => (
          <li key={index} className="text-sm text-zinc-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400/50" />
            {cta}
          </li>
        ))}
      </ul>
    </div>
    <div className="p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
      <h3 className="text-sm font-medium text-white mb-3">Platform Strategy</h3>
      <div className="space-y-3">
        {Object.entries(data?.content_recommendations?.platform_specific || {}).map(([platform, strategy]) => (
          <div key={platform} className="text-sm">
            <span className="text-zinc-400 capitalize">{platform}</span>
            <p className="text-white">{strategy.frequency}</p>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default InstagramProfile;