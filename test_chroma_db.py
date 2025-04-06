import chromadb
client = chromadb.PersistentClient(path="db_path")  # or HttpClient for remote
collection = client.get_collection("food_nutrition")


# Get all entries (IDs, embeddings, metadata, documents)
all_entries = collection.get()
print(all_entries)



# Get entries with specific metadata
filtered_entries = collection.get(
    where={"food_type": "bread"},  # Metadata filter
    where_document={"$contains": "whole wheat"}  # Document content filter
)

# count entries
entry_count = collection.count()
print(f"Total entries: {entry_count}")



# View first N entries
sample_entries = collection.peek(limit=5)


collection.add(
    ids=["bread_001", "apple_001"],
    documents=["Whole wheat bread nutrition...", "Apple nutrition..."],
    metadatas=[
        {"food_type": "bread", "measurement": "slice"},
        {"food_type": "fruit", "measurement": "piece"}
    ],
    embeddings=[[...], [...]]  # Your vectors
)

bread_items = collection.get(
    where={"food_type": "bread"},
    include=["metadatas", "documents"]
)

# Output:
# {
#     'ids': ['bread_001'],
#     'embeddings': None,
#     'documents': ['Whole wheat bread nutrition...'],
#     'metadatas': [{'food_type': 'bread', 'measurement': 'slice'}]
# }



# Create collection
collection = client.create_collection("food_nutrition")

# Add sample data
collection.add(
    ids=["bread_whole_wheat"],
    documents="Per slice: 80 kcal, 3g protein, 1g fat, 15g carbs",
    metadatas={"type": "bread", "base_unit": "slice"},
    embeddings=your_embedding_function("whole wheat bread")
)

# Check entries
results = collection.get(
    where={"type": "bread"},
    include=["documents", "metadatas"]
)

