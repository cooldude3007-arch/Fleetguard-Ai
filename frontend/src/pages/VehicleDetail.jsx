import { useEffect, useState } from "react";
import api from "../services/api";

function VehicleDetail({
  vin,
  partCode,
  onBack
}) {
  const [prediction, setPrediction] = useState(null);
  const [rul, setRul] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchData();
  }, [vin, partCode]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const predictionResponse =
        await api.get(
          `/predictions/${vin}/${partCode}`
        );

      const rulResponse =
        await api.get(
          `/rul/${vin}/${partCode}`
        );

      setPrediction(
        predictionResponse.data
      );

      setRul(
        rulResponse.data
      );

    } catch (error) {
      console.error(error);

      setError(
        "Could not load vehicle details."
      );

    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <p>Loading vehicle details...</p>;
  }

  if (error) {
    return (
      <div>
        <button onClick={onBack}>
          Back
        </button>

        <p>{error}</p>
      </div>
    );
  }

  return (
    <div>
      <button onClick={onBack}>
        ← Back to Predictions
      </button>

      <h1>
        Vehicle Risk Detail
      </h1>

      <h3>
        VIN: {vin}
      </h3>

      <h3>
        Part: {prediction.part_name}
      </h3>

      <h3>
        Part Code: {prediction.part_code}
      </h3>

      <hr />

      <h2>
        Current Risk
      </h2>

      <p>
        Failure Probability:{" "}
        <strong>
          {prediction.failure_probability}%
        </strong>
      </p>

      <p>
        Risk Tier:{" "}
        <strong>
          {prediction.risk_tier}
        </strong>
      </p>

      <hr />

      <h2>
        Remaining Useful Life
      </h2>

      <p>
        Component Status:{" "}
         <strong>
         {rul.replacement_status}
        </strong>
      </p>

      <p>
        Current Component Mileage:{" "}
        <strong>
         {rul.current_part_km} km
        </strong>
      </p>

      <p>
        RUL:
        {" "}
        <strong>
          {rul.rul_km} km
        </strong>
      </p>

      <p>
        Estimated Days:
        {" "}
        <strong>
          {rul.rul_days} days
        </strong>
      </p>

      <p>
        Service Recommendation:
        {" "}
        <strong>
          {rul.estimated_window}
        </strong>
      </p>

      <hr />

      <h2>
        Top Contributing Signals
      </h2>

      <table
        border="1"
        cellPadding="8"
      >
        <thead>
          <tr>
            <th>Signal</th>
            <th>Value</th>
            <th>Weight</th>
            <th>Contribution</th>
          </tr>
        </thead>

        <tbody>
          {prediction.top_signals.map(
            (signal) => (
              <tr key={signal.signal}>
                <td>
                  {signal.signal}
                </td>

                <td>
                  {signal.value}
                </td>

                <td>
                  {(
                    signal.weight * 100
                  ).toFixed(2)}
                  %
                </td>

                <td>
                  {(
                    signal.contribution * 100
                  ).toFixed(2)}
                  %
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>

      <hr />

      <h2>
        Current Telematics
      </h2>

      <table
        border="1"
        cellPadding="8"
      >
        <thead>
          <tr>
            <th>Signal</th>
            <th>Current Value</th>
          </tr>
        </thead>

        <tbody>
          {Object.entries(
            prediction.current_signals
          ).map(
            ([signal, value]) => (
              <tr key={signal}>
                <td>{signal}</td>
                <td>{value}</td>
              </tr>
            )
          )}
        </tbody>
      </table>

      <hr />

      <h2>
        Probability Trend
      </h2>

      <table
        border="1"
        cellPadding="8"
      >
        <thead>
          <tr>
            <th>Week</th>
            <th>Probability</th>
            <th>Risk Tier</th>
          </tr>
        </thead>

        <tbody>
          {prediction.probability_trend.map(
            (item) => (
              <tr
                key={item.week_start_date}
              >
                <td>
                  {item.week_start_date}
                </td>

                <td>
                  {
                    item.failure_probability
                  }
                  %
                </td>

                <td>
                  {item.risk_tier}
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>
    </div>
  );
}

export default VehicleDetail;