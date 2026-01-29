from . import appCalled
from Config import Configs
from Libraries import Faiss_ChunkMapping as chunkMapper


## ==============================
## CONFIGURATION
## ==============================

#### HARD CODE
service = "Categories"
infilename = "HNMU"
jsonKey = "paragraphs"
jsonField = "Text"
dropFields = ["Index"]

MODEL_DIR = "Models"
MODEL_SUMARY = "Summarizer"
MODEL_ENCODE = "Sentence_Transformer"


#### LOAD CONFIG
config = Configs.ConfigValues(pdfname=infilename, service=service)

pdfPath = config["pdfPath"]
exceptPath = config["exceptPath"]
markerPath = config["markerPath"]
statusPath = config["statusPath"]

rawDataPath = config["rawDataPath"]
rawLvlsPath = config["rawLvlsPath"]
structsPath = config["structsPath"]
segmentPath = config["segmentPath"]
schemaPath = config["schemaPath"]
faissPath = config["faissPath"]
mappingPath = config["mappingPath"]
mapDataPath = config["mapDataPath"]
mapChunkPath = config["mapChunkPath"]
metaPath = config["metaPath"]

serviceSegmentPath = config["serviceSegmentPath"]
serviceFaissPath = config["serviceFaissPath"]
serviceMappingPath = config["serviceMappingPath"]
serviceMapDataPath = config["serviceMapDataPath"]
serviceMapChunkPath = config["serviceMapChunkPath"]
serviceMetaPath = config["serviceMetaPath"]

DATA_KEY = config["DATA_KEY"]
EMBE_KEY = config["EMBE_KEY"]
SEARCH_EGINE = config["SEARCH_EGINE"]
RERANK_MODEL = config["RERANK_MODEL"]
RESPON_MODEL = config["RESPON_MODEL"]
EMBEDD_MODEL = config["EMBEDD_MODEL"]
CHUNKS_MODEL = config["CHUNKS_MODEL"]
SUMARY_MODEL = config["SUMARY_MODEL"]
WORD_LIMIT = config["WORD_LIMIT"]

EMBEDD_CACHED_MODEL = f"{MODEL_DIR}/{MODEL_ENCODE}/{EMBEDD_MODEL}"
CHUNKS_CACHED_MODEL = F"{MODEL_DIR}/{MODEL_ENCODE}/{CHUNKS_MODEL}"
SUMARY_CACHED_MODEL = f"{MODEL_DIR}/{MODEL_SUMARY}/{SUMARY_MODEL}"

MAX_INPUT = 1024
MAX_TARGET = 256
MIN_TARGET = 64
TRAIN_EPOCHS = 3
LEARNING_RATE = 3e-5
WEIGHT_DECAY = 0.01
BATCH_SIZE = 4


## ==============================
## SERVER DATA LOAD
## ==============================
print("Server is starting, loading main search index...")
try:
    gReadedData = appCalled.ReadData(segmentPath, faissPath, mappingPath, mapDataPath, mapChunkPath)
    gSegmentDict = gReadedData.get("segmentDict")
    gFaissIndex = gReadedData.get("faissIndex")
    gMapping = gReadedData.get("mapping")
    gMapData = gReadedData.get("mapData")
    gMapChunk = gReadedData.get("mapChunk")
    
    if gFaissIndex:
        print(f"[SUCCESS] Main search index '{infilename}' loaded successfully.")
    else:
        print(f"[FAILED] Could not load main search index from {faissPath}.")
        
except Exception as e:
    print(f"[CRITICAL] Failed to load main search index: {e}")
    gFaissIndex = None

print("Loading 'Categories' index for classification...")
try:
    gServiceData = appCalled.ReadData(
        serviceSegmentPath, 
        serviceFaissPath, 
        serviceMappingPath, 
        serviceMapDataPath, 
        serviceMapChunkPath
    )
    gServiceSegmentDict = gServiceData.get("segmentDict")
    gServiceFaissIndex = gServiceData.get("faissIndex")
    gServiceMapping = gServiceData.get("mapping")
    gServiceMapData = gServiceData.get("mapData")
    gServiceMapChunk = gServiceData.get("mapChunk")
    
    if gServiceFaissIndex:
        print("[SUCCESS] 'Categories' index loaded successfully.")
    else:
        print("[FAILED] Could not load 'Categories' index.")

except Exception as e:
    print(f"[CRITICAL] Failed to load 'Categories' index: {e}")
    gServiceFaissIndex = None

## ==============================
## API PIPELINE FUNCTIONS
## ==============================

def processPdfPipeline(pdf_bytes):
    """
    Pipeline cho endpoint /process_pdf.
    Nhận PDF bytes -> tóm tắt -> phân loại.
    """
    print("Processing new PDF...")
    # 1. Trích xuất
    rawDataDict = appCalled.preReadPDF(pdfPath=None, pdfBytes=pdf_bytes)
    if rawDataDict is None:
        print("PDF quality check failed or extraction failed.")
        return {
            "checkstatus": "failed",
            "summary": "",
            "category": "PDF không hợp lệ hoặc không thể trích xuất"
        }

    # 2. Tóm tắt
    print("Summarizing PDF...")
    summaryText = appCalled.summarizeDcmt(rawDataDict)
    
    print("Classifying PDF...")
    if not gServiceFaissIndex:
        print("Cannot classify: 'Categories' index not loaded.")
        bestArticle = "Không thể phân loại (chưa tải index)"
    else:
        searchRes = appCalled.runSearch(summaryText, gServiceFaissIndex, gServiceMapping, gServiceMapData, gServiceMapChunk)
        reranked = appCalled.runRerank(summaryText, searchRes)
        bestCategory = appCalled.chunkMap(reranked, gServiceSegmentDict, dropFields, fields=["Article"], nChunks=1)

        bestArticles = [item["fields"].get("Article") for item in bestCategory["extractedFields"]]
        bestArticle = bestArticles[0] if bestArticles else "Không xác định"

    print(f"Done. Summary: {len(summaryText)} chars, Category: {bestArticle}")
    return {
        "checkstatus": "ok",
        "summary": summaryText,
        "category": bestArticle,
    }


def searchPipeline(queryText, k=10):
    """
    Pipeline cho endpoint /search.
    Nhận query -> tìm kiếm trên index chính.
    """
    print(f"Searching for: '{queryText}'")
    if not gFaissIndex:
        print("Không thể tìm kiếm: Chưa tải index")
        return []

    searchRes = appCalled.runSearch(queryText, gFaissIndex, gMapping, gMapData, gMapChunk)
    reranked = appCalled.runRerank(queryText, searchRes)
    chunkReturn = appCalled.chunkMap(reranked, gSegmentDict, dropFields, fields=None, nChunks=k)
    return chunkReturn.get("extractedFields", [])