function FlightCard({ flight }) {
  return (
    <div className="flight-card">
      <div className="flight-card-header">
        <h3>{flight.airline}</h3>
        <h3 className="price-text">${flight.price}</h3>
      </div>

      <p>
        <strong>Route:</strong> {flight.from_city} → {flight.to_city}
      </p>

      <p>
        <strong>Date:</strong> {flight.date}
      </p>

      <p>
        <strong>Departure:</strong> {flight.departure_time}
      </p>

      <p>
        <strong>Arrival:</strong> {flight.arrival_time}
      </p>

      <p>
        <strong>Duration:</strong> {flight.duration}
      </p>

      <p>
        <strong>Stops:</strong> {flight.stops}
      </p>

      <p>
        <strong>Layover:</strong> {flight.layover} hrs
      </p>

      <p>
        <strong>Class:</strong> {flight.ticket_class}
      </p>
    </div>
  );
}

export default FlightCard;