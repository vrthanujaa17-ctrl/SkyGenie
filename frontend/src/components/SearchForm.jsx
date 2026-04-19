function SearchForm({
  fromCity,
  toCity,
  departureDate,
  maxPrice,
  maxStops,
  maxLayover,
  sortBy,
  setFromCity,
  setToCity,
  setDepartureDate,
  setMaxPrice,
  setMaxStops,
  setMaxLayover,
  setSortBy,
  searchFlights,
  error,
}) {
  return (
    <div className="search-box">
      <h2>Search Flights</h2>

      <div className="form-row">
        <input
          type="text"
          placeholder="From City"
          value={fromCity}
          onChange={(e) => setFromCity(e.target.value)}
        />

        <input
          type="text"
          placeholder="To City"
          value={toCity}
          onChange={(e) => setToCity(e.target.value)}
        />

        <input
          type="date"
          value={departureDate}
          onChange={(e) => setDepartureDate(e.target.value)}
        />
      </div>

      <div className="form-row">
        <input
          type="number"
          placeholder="Max Price"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
        />

        <input
          type="number"
          placeholder="Max Stops"
          value={maxStops}
          onChange={(e) => setMaxStops(e.target.value)}
        />

        <input
          type="number"
          placeholder="Max Layover (hrs)"
          value={maxLayover}
          onChange={(e) => setMaxLayover(e.target.value)}
        />
      </div>

      <div className="form-row">
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="">Sort By</option>
          <option value="price">Cheapest First</option>
          <option value="stops">Fewest Stops</option>
          <option value="layover">Shortest Layover</option>
          <option value="duration">Shortest Duration</option>
        </select>
      </div>

      <button onClick={searchFlights}>Search</button>

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

export default SearchForm;