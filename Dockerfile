FROM ollama/ollama:latest

# Expose the Ollama API port
EXPOSE 11434

# Set the entrypoint to the Ollama server
ENTRYPOINT ["/bin/ollama"]
CMD ["serve"] 