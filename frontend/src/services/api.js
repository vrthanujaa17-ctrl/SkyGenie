export const fetchFlights = async (queryString) => {
  const response = await fetch(`http://127.0.0.1:5001/flights?${queryString}`);

  if (!response.ok) {
    throw new Error("Failed to fetch flights");
  }

  return response.json();
};
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5001';

export const fetchLandmarks = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/landmarks`);
        return response.data;
    } catch (error) {
        console.error("Error fetching landmarks:", error);
        return [];
    }
};