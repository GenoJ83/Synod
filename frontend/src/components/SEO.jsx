import { Helmet } from 'react-helmet-async';

const DEFAULT_TITLE = 'Synod.ai - AI Lecture Analysis';
const DEFAULT_DESCRIPTION = 'AI-powered lecture material analysis. Extract concepts, generate summaries, and test knowledge instantly.';
const DEFAULT_KEYWORDS = 'lecture notes, AI summary, concept extraction, student study tool, PDF analysis, PPTX OCR';
const BASE_URL = 'https://synod-phi.vercel.app';

export default function SEO({ title, description, keywords, ogTitle, ogDescription, ogImage, ogUrl, twitterTitle, twitterDescription, twitterImage }) {
  return (
    <Helmet>
      {title && <title>{title}</title>}
      {title && <meta property="og:title" content={ogTitle || title} />}
      {title && <meta name="twitter:title" content={twitterTitle || title} />}
      
      <meta name="description" content={description || DEFAULT_DESCRIPTION} />
      <meta property="og:description" content={ogDescription || description || DEFAULT_DESCRIPTION} />
      <meta name="twitter:description" content={twitterDescription || description || DEFAULT_DESCRIPTION} />
      
      <meta name="keywords" content={keywords || DEFAULT_KEYWORDS} />
      
      <meta property="og:image" content={ogImage ? `${BASE_URL}${ogImage}` : `${BASE_URL}/logo.png`} />
      <meta property="og:url" content={ogUrl ? `${BASE_URL}${ogUrl}` : BASE_URL} />
      <meta property="og:type" content="website" />
      
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:image" content={twitterImage ? `${BASE_URL}${twitterImage}` : `${BASE_URL}/logo.png`} />
    </Helmet>
  );
}
