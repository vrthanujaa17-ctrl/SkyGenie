import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

function Results() {
  const location = useLocation();
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);

  const from = params.get("from") || "NYC";
  const to = params.get("to") || "LAX";
  const date = params.get("date") || "2026-06-15";
  const returnDate = params.get("returnDate") || "";
  const maxPrice = params.get("maxPrice") || "";
  const maxStops = params.get("maxStops") || "";
  const maxLayover = params.get("maxLayover") || "";
  const sortBy = params.get("sortBy") || "price";

  const [flights, setFlights] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [usingFallback, setUsingFallback] = useState(false);

  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([]);

  const cityMap = {
    LAX: "LOS ANGELES",
    JFK: "NEW YORK",
    NYC: "NEW YORK",
    SFO: "SAN FRANCISCO",
    ORD: "CHICAGO",
    CDG: "PARIS",
    FCO: "ROME",
  };

  const destinationImages = {
    "LOS ANGELES": "/images/losangeles.jpeg",
    "NEW YORK": "/images/newyork.jpeg",
    "SAN FRANCISCO": "/images/sanfrancisco.jpeg",
    CHICAGO: "/images/chicago.jpeg",
    PARIS: "/images/paris.jpeg",
    ROME: "/images/rome.jpeg",
  };

  const normalizedDestination =
    cityMap[to.toUpperCase()] || to.toUpperCase();

  const destinationImage =
    destinationImages[normalizedDestination] || "/images/default.jpeg";

  useEffect(() => {
    const searchFlights = async () => {
      setLoading(true);
      setError("");
      setInfoMessage("");
      setUsingFallback(false);

      try {
        const API_BASE = "http://127.0.0.1:5001";
        const response = await fetch(
          `${API_BASE}/flights?from=${encodeURIComponent(
            from
          )}&to=${encodeURIComponent(to)}&date=${encodeURIComponent(date)}`
        );

        const data = await response.json();

        if (!response.ok) {
          setFlights(data.fallback || []);
          setUsingFallback(true);
          setError(data.error || "Request failed.");
          return;
        }

        setFlights(data.flights || data.fallback || []);
        setUsingFallback(Boolean(data.fallback_used));
        setInfoMessage(data.message || "");
      } catch (err) {
        setError("Could not connect to backend.");
      } finally {
        setLoading(false);
      }
    };

    searchFlights();
  }, [from, to, date]);

  const cleanBotText = (text) => {
    if (!text) return "";
    return text
      .replace(/\*\*/g, "")
      .replace(/\r/g, "")
      .trim();
  };

  const renderBotMessage = (text) => {
    const cleaned = cleanBotText(text);
    const sections = cleaned
      .split(/\n\s*\n/)
      .map((section) => section.trim())
      .filter(Boolean);

    return sections.map((section, index) => {
      const lines = section
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);

      if (lines.length === 0) return null;

      const firstLine = lines[0];
      const isHeading =
        /^day\s*\d+/i.test(firstLine) ||
        /itinerary/i.test(firstLine) ||
        /tips/i.test(firstLine) ||
        /budget/i.test(firstLine) ||
        /food/i.test(firstLine) ||
        /transport/i.test(firstLine);

      return (
        <div key={index} className="bot-section-card">
          {isHeading ? (
            <h4 className="bot-section-title">{firstLine}</h4>
          ) : (
            <p className="bot-section-text">{firstLine}</p>
          )}

          {lines.slice(isHeading ? 1 : 1).map((line, i) => {
            const bulletLine = line.replace(/^[-•]\s*/, "");
            return (
              <p key={i} className="bot-section-text">
                {line.startsWith("-") || line.startsWith("•") ? `• ${bulletLine}` : line}
              </p>
            );
          })}
        </div>
      );
    });
  };

  const sendMessage = async () => {
    if (!chatInput.trim()) return;

    const newMessages = [...messages, { role: "user", text: chatInput }];
    setMessages(newMessages);
    setChatInput("");

    try {
      const res = await fetch("http://127.0.0.1:5001/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: chatInput }),
      });

      const data = await res.json();

      setMessages([
        ...newMessages,
        { role: "bot", text: data.answer || "No response received." },
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        { role: "bot", text: "Chat error. Check backend." },
      ]);
    }
  };

  const formatTime = (dt) => dt?.split("T")[1]?.slice(0, 5) || "N/A";

  const getNumericPrice = (p) =>
    parseFloat(String(p).replace(/[^0-9.]/g, "")) || 0;

  const filteredAndSortedFlights = useMemo(() => {
    let result = [...flights];

    if (maxPrice !== "") {
      result = result.filter(
        (f) => getNumericPrice(f.price) <= Number(maxPrice)
      );
    }

    if (maxStops !== "") {
      result = result.filter(
        (f) => Number(f.stopCount) <= Number(maxStops)
      );
    }

    if (maxLayover !== "") {
      result = result.filter(
        (f) => Number(f.layoverMinutes) <= Number(maxLayover)
      );
    }

    if (sortBy === "price") {
      result.sort(
        (a, b) => getNumericPrice(a.price) - getNumericPrice(b.price)
      );
    } else if (sortBy === "duration") {
      result.sort(
        (a, b) => (a.durationMinutes || 0) - (b.durationMinutes || 0)
      );
    }

    return result;
  }, [flights, maxPrice, maxStops, maxLayover, sortBy]);

  return (
    <div className="results-shell">
      <div className="results-content">
        <button onClick={() => navigate("/")} className="back-btn">
          ← Back to Search
        </button>

        <h1>Flight Results</h1>

        <p className="subtitle results-subtitle">
          Showing results for <strong>{from}</strong> →{" "}
          <strong>{normalizedDestination}</strong> on{" "}
          <strong>{date}</strong>
          {returnDate && (
            <>
              {" "}
              with return on <strong>{returnDate}</strong>
            </>
          )}
        </p>

        <section className="destination-preview-section">
          <div className="destination-preview-card">
            <img
              className="destination-preview-image"
              src={destinationImage}
              alt={normalizedDestination}
            />
            <div className="destination-preview-content">
              <h3>{normalizedDestination}</h3>
              <p>
                <strong>Destination Preview</strong>
              </p>
            </div>
          </div>
        </section>

        {error && <p className="error-message">{error}</p>}
        {infoMessage && (
          <p className={`info-message ${usingFallback ? "warning" : "success"}`}>
            {infoMessage}
          </p>
        )}

        <h2>Available Flights</h2>

        {loading ? (
          <p className="center-text">Searching flights...</p>
        ) : (
          <div className="results-list">
            {filteredAndSortedFlights.length > 0 ? (
              filteredAndSortedFlights.map((flight, index) => (
                <div key={index} className="flight-card">
                  <div className="flight-header">
                    <h3>{flight.airline}</h3>
                    <h3>{flight.price}</h3>
                  </div>
                  <p>
                    {flight.origin} → {flight.destination}
                  </p>
                  <p>Departure: {formatTime(flight.departureTime)}</p>
                  <p>Arrival: {formatTime(flight.arrivalTime)}</p>
                  <p>Stops: {flight.stopCount}</p>
                  <p>Layover: {flight.layoverMinutes} mins</p>
                  <p>Duration: {flight.durationMinutes} mins</p>
                </div>
              ))
            ) : (
              <p className="center-text">No flights found.</p>
            )}
          </div>
        )}
      </div>

      <div className="chat-sidebar">
        {chatOpen ? (
          <div className="chat-window fixed-chat-window large-chat">
            <div className="chat-header-row">
              <span>✈️ Travel Assistant</span>
              <button
                className="chat-close-btn"
                onClick={() => setChatOpen(false)}
              >
                ✖
              </button>
            </div>

            <div className="chat-messages">
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  {m.role === "bot" ? renderBotMessage(m.text) : m.text}
                </div>
              ))}
            </div>

            <div className="chat-input-area">
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about your destination..."
              />
              <button onClick={sendMessage}>Send</button>
            </div>
          </div>
        ) : (
          <button
            className="chat-toggle side-chat-toggle"
            onClick={() => setChatOpen(true)}
          >
            💬 Ask Travel Bot
          </button>
        )}
      </div>
    </div>
  );
}

export default Results;