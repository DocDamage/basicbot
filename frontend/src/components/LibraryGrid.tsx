import { useState, useEffect } from 'react';
import axios from 'axios';
import { Book, Search, RefreshCw, BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';

// Types (should be in separate file ideally)
interface BookData {
    id: string;
    title: string;
    author: string;
    cover_image_path: string;
}

interface LibraryGridProps {
    onSelectBook: (bookId: string) => void;
    onClose: () => void;
}

export function LibraryGrid({ onSelectBook, onClose }: LibraryGridProps) {
    const [books, setBooks] = useState<BookData[]>([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);

    const fetchBooks = async () => {
        setLoading(true);
        try {
            // Use port 8001
            const res = await axios.get(`http://localhost:8001/api/library?search=${search}&page=${page}`);
            setBooks(res.data.books);
        } catch (err) {
            console.error("Library fetch failed", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBooks();
    }, [search, page]);

    const triggerScan = async () => {
        await axios.post('http://localhost:8001/api/library/scan');
        alert("Scan started in background...");
    };

    return (
        <div className="library-overlay">
            <div className="library-header">
                <h2><span className="icon">📚</span> Neural Library</h2>
                <div className="library-controls">
                    <div className="search-box">
                        <Search size={14} />
                        <input
                            type="text"
                            placeholder="Search knowledge base..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <button className="icon-btn" onClick={triggerScan} title="Rescan Library">
                        <RefreshCw size={18} />
                    </button>
                    <button className="icon-btn" onClick={onClose}>✖</button>
                </div>
            </div>

            <div className="library-content">
                {loading && <div className="loading-spinner">Accessing Database...</div>}

                <div className="books-grid">
                    {books.map((book) => (
                        <motion.div
                            key={book.id}
                            className="book-card"
                            layoutId={book.id}
                            onClick={() => onSelectBook(book.id)}
                            whileHover={{ scale: 1.05 }}
                        >
                            <div className="cover-wrapper">
                                {book.cover_image_path ? (
                                    <img src={book.cover_image_path} alt={book.title} />
                                ) : (
                                    <div className="placeholder-cover">
                                        <BookOpen size={30} />
                                        <span>{book.title[0]}</span>
                                    </div>
                                )}
                            </div>
                            <div className="book-info">
                                <h3>{book.title}</h3>
                                <p>{book.author}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
