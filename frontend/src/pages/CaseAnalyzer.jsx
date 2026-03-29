import { useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, FileText, Upload, AlertCircle, Scale, X, FileUp } from 'lucide-react'

export default function CaseAnalyzer() {
    const [file, setFile] = useState(null)
    const [query, setQuery] = useState('')
    const [loading, setLoading] = useState(false)
    const [response, setResponse] = useState(null)
    const [error, setError] = useState(null)
    const fileInputRef = useRef(null)

    const handleFileChange = (e) => {
        const selected = e.target.files[0]
        if (selected) {
            setFile(selected)
            setResponse(null)
            setError(null)
        }
    }

    const clearFile = () => {
        setFile(null)
        setQuery('')
        setResponse(null)
        setError(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }

    const handleSubmit = async (e) => {
        e?.preventDefault()
        const q = query.trim()
        if (!q || !file || loading) return

        setLoading(true)
        setError(null)
        setResponse(null)

        const formData = new FormData()
        formData.append('file', file)
        formData.append('query', q)

        try {
            const res = await fetch('/api/analyze_case', {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                throw new Error(errData.detail || `Server returned ${res.status}`)
            }

            const data = await res.json()
            setResponse(data)
        } catch (err) {
            setError(err.message || 'Something went wrong while analyzing the case.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            <section className="hero" style={{ paddingBottom: '2rem' }}>
                <div className="hero-content">
                    <div className="hero-badge">
                        <FileText size={14} /> Document AI
                    </div>
                    <h1>
                        Analyze Your <span className="highlight">Case Files</span>
                    </h1>
                    <p className="hero-subtitle">
                        Upload a PDF or TXT document (e.g., judgment, brief, FIR) and ask questions. 
                        Jolly LLB will extract facts and analyze the document instantly.
                    </p>
                </div>
            </section>

            <section className="query-section">
                {!file ? (
                    <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
                        <input
                            type="file"
                            accept=".pdf, .txt"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            style={{ display: 'none' }}
                        />
                        <Upload size={32} color="var(--text-tertiary)" className="upload-icon" />
                        <h3>Upload Document</h3>
                        <p>Click to select a PDF or TXT file</p>
                    </div>
                ) : (
                    <div className="active-file-card">
                        <div className="active-file-info">
                            <FileUp size={24} color="#8b5cf6" />
                            <div>
                                <h4>{file.name}</h4>
                                <span className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                            </div>
                        </div>
                        <button className="icon-btn" onClick={clearFile} aria-label="Clear File">
                            <X size={20} />
                        </button>
                    </div>
                )}

                {file && (
                    <form onSubmit={handleSubmit} style={{ marginTop: '1.5rem' }}>
                        <div className="query-box">
                            <div className="query-input-row">
                                <FileText size={18} color="var(--text-tertiary)" style={{ marginLeft: 12, flexShrink: 0 }} />
                                <input
                                    id="query-input"
                                    type="text"
                                    placeholder="E.g., What are the main arguments presented?"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    autoComplete="off"
                                />
                                <button
                                    id="query-submit"
                                    type="submit"
                                    className="query-submit-btn"
                                    disabled={loading || query.trim().length < 3}
                                >
                                    {loading ? (
                                        <>Analyzing...</>
                                    ) : (
                                        <>
                                            <Send size={16} /> Analyze
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </form>
                )}
            </section>

            {loading && (
                <div className="response-section">
                    <div className="response-card">
                        <div className="typing-indicator">
                            <div className="typing-dots">
                                <div className="typing-dot" />
                                <div className="typing-dot" />
                                <div className="typing-dot" />
                            </div>
                            <span className="typing-text">Parsing document and generating answer...</span>
                        </div>
                    </div>
                </div>
            )}

            {error && !loading && (
                <div className="response-section">
                    <div className="error-card">
                        <AlertCircle size={20} />
                        <div className="error-card-content">
                            <h4>Analysis Failed</h4>
                            <p>{error}</p>
                        </div>
                    </div>
                </div>
            )}

            {response && !loading && (
                <div className="response-section">
                    <div className="response-card">
                        <div className="response-header">
                            <div className="response-header-left">
                                <div className="response-avatar">
                                    <Scale size={16} color="#0a0e17" />
                                </div>
                                <span className="response-header-label">Case Analysis</span>
                            </div>
                        </div>
                        <div className="response-body">
                            <div className="response-answer">
                                <ReactMarkdown>{response.answer}</ReactMarkdown>
                            </div>
                            {response.sources && response.sources.length > 0 && (
                                <div className="response-sources">
                                    <div className="response-sources-title">Referenced Context</div>
                                    <div className="source-chips">
                                        {response.sources.map((src, i) => (
                                            <span key={i} className="source-chip" style={{ borderColor: '#8b5cf640' }}>
                                                <FileText size={14} style={{ color: '#8b5cf6' }} />
                                                <span style={{ color: '#8b5cf6', fontWeight: 600, marginRight: 4 }}>
                                                    {src.title}
                                                </span>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
