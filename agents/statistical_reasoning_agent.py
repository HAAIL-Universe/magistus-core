# statistical_reasoning_agent.py
import numpy as np
import scipy.stats as stats

class StatisticalReasoningAgent:
    def __init__(self, historical_data=None):
        """
        Initialize the agent with optional historical data.
        The data should be a list of previous data points (numerical).
        """
        self.historical_data = historical_data or []
    
    def update_data(self, new_data):
        """
        Add new data to the historical dataset for future predictions.
        Each new_data should be a single data point (numeric).
        """
        self.historical_data.append(new_data)
    
    def predict(self):
        """
        Make probabilistic predictions based on historical data using 
        a normal distribution.
        
        Returns:
            predicted_outcome (float): The most probable future outcome.
        """
        if not self.historical_data:
            print("No data available for prediction.")
            return None
        
        # Convert the historical data into a numpy array
        data = np.array(self.historical_data)
        
        # Compute the mean and standard deviation of the data
        mean, std = np.mean(data), np.std(data)
        
        # Compute the probability density function for future outcomes
        future_probability = stats.norm.pdf(data, mean, std)
        
        # Return the most probable future outcome (highest probability)
        predicted_outcome = data[np.argmax(future_probability)]
        return predicted_outcome
    
    def risk_assessment(self):
        """
        Calculate a risk score based on the standard deviation of historical data.
        The higher the standard deviation, the higher the risk.
        
        Returns:
            risk (float): The standard deviation representing the risk.
        """
        if not self.historical_data:
            print("No data available for risk assessment.")
            return None
        
        data = np.array(self.historical_data)
        
        # Calculate risk based on the standard deviation
        risk = np.std(data)  # Risk is defined as variance in the data
        return risk


class ReasoningPipeline:
    def __init__(self, agents):
        """
        Initialize the reasoning pipeline with a list of agents, including the statistical reasoning agent.
        """
        self.agents = agents  # A list of all agents, including StatisticalReasoningAgent
    
    def process(self, input_data):
        """
        Process input data through all agents, including the statistical reasoning agent.
        
        Returns:
            agent_outputs (list): Outputs from all agents
            prediction (float): Predicted outcome from the Statistical Reasoning Agent
            risk (float): Risk score from the Statistical Reasoning Agent
        """
        agent_outputs = []
        
        # Process the input data through all agents
        for agent in self.agents:
            output = agent.process(input_data)  # Assuming each agent has a `process` method
            agent_outputs.append(output)
        
        # Retrieve the Statistical Reasoning Agent and get predictions and risk
        stat_agent = next(agent for agent in self.agents if isinstance(agent, StatisticalReasoningAgent))
        prediction = stat_agent.predict()
        risk = stat_agent.risk_assessment()
        
        return agent_outputs, prediction, risk
