
import sys
import os
sys.path.insert(0, os.getcwd())

from app.nlp.summarizer import Summarizer

def repro():
    # Snippet provided by user (likely the beginning of the text)
    text = """
    Query-focused and Memory-aware Reranker for Long Context Processing 
    Yuqing Li1,2* Jiangnan Li3* Mo Yu3* Guoxuan Ding1,2 Zheng Lin1,2† Weiping Wang1 Jie Zhou3 
    1Institute of Information Engineering, Chinese Academy of Sciences, Beijing, China 
    2School of Cyber Security, University of Chinese Academy of Sciences, Beijing, China 
    3Westlake University, Hangzhou, China 
    {liyuqing, dingguoxuan, linzheng, wangweiping}@iie.ac.cn 
    {lijiangnan, yumo, zhoujie}@westlake.edu.cn
    
    Abstract
    Reranking is an essential component in Retrieval-Augmented Generation (RAG) to bridge the gap between retrieval and generation. 
    However, existing rerankers often struggle with long context due to the quadratic complexity of self-attention and the limited window size. 
    In this paper, we propose QRRanker, a Query-focused and Memory-aware Reranker that efficiently processes long context by...
    """
    
    # Force a failure to test fallback logic
    s.has_transformers = True
    def dummy_summarize(*args, **kwargs):
        raise RuntimeError("Simulated OOM or model error")
    s.model.generate = dummy_summarize

    print("Initializing Summarizer with Pegasus model...")
    s = Summarizer(model_name="UNIST-Eunchan/Research-Paper-Summarization-Pegasus-x-ArXiv")
    
    print("\nAttempting to summarize...")
    try:
        result = s.summarize(text)
        print("\n--- Summary ---")
        print(result["summary"])
        print("\n--- Metrics ---")
        print(result["metrics"])
    except Exception as e:
        print(f"\nCaught exception in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    repro()
