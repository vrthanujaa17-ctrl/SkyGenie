import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  const [from, setFrom] = useState("NYC");
  const [to, setTo] = useState("LAX");
  const [departureDate, setDepartureDate] = useState("");
  const [returnDate, setReturnDate] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [maxStops, setMaxStops] = useState("");
  const [maxLayover, setMaxLayover] = useState("");
  const [sortBy, setSortBy] = useState("price");

  const handleSearch = () => {
    navigate(
      `/results?from=${encodeURIComponent(from)}&to=${encodeURIComponent(
        to
      )}&date=${encodeURIComponent(
        departureDate
      )}&returnDate=${encodeURIComponent(
        returnDate
      )}&maxPrice=${encodeURIComponent(
        maxPrice
      )}&maxStops=${encodeURIComponent(
        maxStops
      )}&maxLayover=${encodeURIComponent(
        maxLayover
      )}&sortBy=${encodeURIComponent(sortBy)}`
    );
  };

  return (
    <div className="home-bg">
      <div className="container">
        <h1>✈️ SkyGenie</h1>
        <p className="subtitle">
          Your smart travel companion for finding the best flights✨
        </p>

        <div className="search-box">
          <div className="input-group">
            <label>From</label>
            <input
              value={from}
              onChange={(e) => setFrom(e.target.value.toUpperCase())}
              placeholder="Enter city or airport"
            />
          </div>

          <div className="input-group">
            <label>To</label>
            <input
              value={to}
              onChange={(e) => setTo(e.target.value.toUpperCase())}
              placeholder="Enter destination"
            />
          </div>

          <div className="input-group">
            <label>Departure Date</label>
            <input
              type="date"
              value={departureDate}
              onChange={(e) => setDepartureDate(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Return Date</label>
            <input
              type="date"
              value={returnDate}
              onChange={(e) => setReturnDate(e.target.value)}
            />
          </div>

          <button onClick={handleSearch}>Search Flights</button>
        </div>

        <div className="search-box">
          <div className="input-group">
            <label>Max Price</label>
            <input
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Max Stops</label>
            <input
              type="number"
              value={maxStops}
              onChange={(e) => setMaxStops(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Max Layover</label>
            <input
              type="number"
              value={maxLayover}
              onChange={(e) => setMaxLayover(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Sort</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="price">Sort by Price</option>
              <option value="duration">Sort by Duration</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;