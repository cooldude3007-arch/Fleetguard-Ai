import { useEffect, useState } from "react";
import api from "../services/api";

function Predictions({ onSelectVehicle }) {
  const [parts, setParts] = useState([]);
  const [selectedPart, setSelectedPart] = useState("");
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchParts();
  }, []);

  const fetchParts = async () => {
    try {
      const response = await api.get("/parts");
      setParts(response.data);

      if (response.data.length > 0) {
        setSelectedPart(response.data[0].part_code);
      }
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    if (selectedPart) {
      fetchPredictions();
    }
  }, [selectedPart]);

  const fetchPredictions = async () => {
    try {
      setLoading(true);

      const response = await api.get(
        `/predictions/${selectedPart}`
      );

      setPredictions(response.data.predictions);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Failure Probability</h1>

      <div>
        <label>Select Part: </label>

        <select
          value={selectedPart}
          onChange={(e) =>
            setSelectedPart(e.target.value)
          }
        >
          {parts.map((part) => (
            <option
              key={part.part_code}
              value={part.part_code}
            >
              {part.part_name}
            </option>
          ))}
        </select>
      </div>

      {loading && <p>Loading...</p>}

      {!loading && (
        <table border="1" cellPadding="8">
          <thead>
            <tr>
              <th>VIN</th>
              <th>Part</th>
              <th>Probability</th>
              <th>Risk Tier</th>
              <th>Top Signal</th>
            </tr>
          </thead>

          <tbody>
            {predictions.map((item) => (
              <tr key={item.vin}>
                <td>
                  <button
                   onClick={() =>
                   onSelectVehicle(
                item.vin,
                item.part_code
                 )
                }
                >
                  {item.vin}
                   </button>
                </td>

                <td>{item.part_code}</td>

                <td>
                  {item.failure_probability}%
                </td>

                <td>
                  {item.risk_tier}
                </td>

                <td>
                  {item.top_signals?.[0]?.signal || "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Predictions;