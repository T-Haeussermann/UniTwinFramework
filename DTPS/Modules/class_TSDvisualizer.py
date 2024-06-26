import json
import time
from queue import Queue
import numpy as np
import scipy
import statsmodels.api as sm
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import base64
from fastapi.responses import StreamingResponse
import matplotlib.pyplot as plt
from joblib import dump, load
from fastapi import APIRouter, BackgroundTasks
from .class_ComponentABC import Component
from .class_Event import Event

class class_TSDvisualizer(Component):
    def __init__(self, _conf):
        self._event = Event()
        self._subscribers = {}
        self.Q = Queue()
        self.initialized = False
        self.data = None
        self.sensors = []
        self.sensorData = {}
        self.dbInstance = None
        self.TSDanalyse = None

        self._router = APIRouter()
        self.configure_router()

        for item in _conf:
            self.__setattr__(item, _conf[item])

    def getData(self, initialization_time):
        # Load the time series data
        self.data = self.dbInstance.query(self.parent._uid, "data_frame", initialization_time,  False)

        # get list of different sensors
        self.sensors = sorted(list(set(self.data["Sensor"].to_list())))
        print(self.data)
        # selecting rows based on condition and create sensordata from it
        for sensor in self.sensors:
            sensor_df = self.data[self.data['Sensor'] == sensor]
            self.sensorData[sensor] = {"data": ""}
            self.sensorData[sensor]["data"] = sensor_df['Value'].reset_index(drop=True)
        print(self.sensorData)

    def getLast(self, sensor):
        # replace new value with last for implementation in unitwin
        # sensor_df = self.data[self.data['Sensor'] == sensor]
        last = self.dbInstance.query(self.parent._uid, "data_frame", 10,  True)
        last = last[last['Sensor'] == sensor]['Value'].reset_index(drop=True)
        self.sensorData[sensor]["last"] = last

    def createModel(self, sensor, data):

        # Fit the SARIMA model to the training data
        model = sm.tsa.SARIMAX(data, order=(2, 0, 0), seasonal_order=(1, 0, 0, 12))
        results = model.fit()

        # save the model using joblib
        dump(results, sensor + '_model.joblib')

    def loadModel(self, sensor):
        # Load the saved model from the file
        results = load(sensor + '_model.joblib')
        return results

    def forcast(self, sensor):
        # get present sensor data and update prediction model
        data = self.dbInstance.query(self.parent._uid, "data_frame", 10, False)
        sensor_df = data[data['Sensor'] == sensor]
        data = sensor_df['Value'][-100:].reset_index(drop=True)
        self.createModel(sensor, data)

        # Load model for sensor
        results = self.loadModel(sensor)

        # Forecast future values using the fitted model
        steps = len(data) #100
        forecast = results.forecast(steps=steps, alpha=0.05) #(steps=len(data), alpha=0.05)

        # Plot the actual values and the forecasted values
        fig, ax = plt.subplots()
        ax.plot(data, label='Actual Data of ' + sensor)
        ax.plot(forecast, label='Forecasted Data')
        ax.legend(loc='upper left')

        # Convert the plot to an image
        buf = io.BytesIO()
        canvas = FigureCanvasAgg(fig)
        canvas.print_png(buf)
        buf.seek(0)
        plt.close(fig)

        # Convert the image to base64
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')

        return image_base64

    def predict(self, sensor=None, plot=False):

            self.getLast(sensor)
            last = self.sensorData[sensor]["last"]
            data = self.sensorData[sensor]["data"]
            point = np.zeros(len(data))

            # Define point to test
            new_x = len(data) - 10
            new_y = last[0]
            point[new_x] = new_y

            # calculate the cross-correlatio between ts and the new point, to find the maximum
            corr = scipy.signal.correlate(data, point, mode="full")
            # error handling if no exact fit is possible
            try:
                delay = np.where(corr == 1)[0][0] - (len(data) - 1)
            except:
                delay = np.argmax(corr) - (len(data) - 1)
                # delay = (np.abs(corr - 1)).argmin() - (len(data) - 1)

            # print the delay
            print(f'The delay between the time series and the new point is {delay} units.')

            # shift the time series by the estimated delay
            ts_shifted = np.roll(data, -delay)

            # calculate mean and standard deviation of the shifted time series
            ts_mean = np.mean(ts_shifted)
            ts_std = np.std(ts_shifted)

            # set significance level as a multiple of the standard deviation
            significance_level = 1

            # check if the new point fits in the time series based on standard
            lower_boundary = ts_shifted[new_x] - ts_std
            upper_boundary = ts_shifted[new_x] + ts_std

            if point[new_x] > lower_boundary and point[new_x] < upper_boundary:
                msg = 'The new point fits in the time series based on standard deviation.'
            else:
                msg = 'The new point does not fit in the time series based on standard deviation.'

            if plot == True:
                return self.plot(sensor,  ts_shifted, new_x, point, ts_std, corr)
            elif plot == False:
                return msg

    def plot(self, sensor, ts_shifted, new_x, point, ts_std, corr):
        fig, axs = plt.subplots(3, 1, figsize=(8, 12))

        axs[0].set_ylabel("ts")
        axs[0].plot(self.sensorData[sensor]['data'])
        axs[0].plot(new_x, point[new_x], 'ro')
        axs[0].set_xlim([0, len(self.sensorData[sensor]['data'])])

        axs[1].set_ylabel("fit")
        axs[1].plot(self.sensorData[sensor]['data'])
        axs[1].plot(ts_shifted)
        axs[1].plot(new_x, point[new_x], 'ro')
        axs[1].fill_between(np.arange(len(self.sensorData[sensor]['data'])), ts_shifted - ts_std,
                            ts_shifted + ts_std, alpha=0.2, label='Standard deviation range')
        axs[1].set_xlim([0, len(ts_shifted)])
        axs[1].legend()

        axs[2].set_ylabel("corr")
        axs[2].plot(corr)
        axs[2].set_xlim([0, len(corr)])

        # Convert the plot to an image
        buf = io.BytesIO()
        canvas = FigureCanvasAgg(fig)
        canvas.print_png(buf)
        buf.seek(0)
        plt.close(fig)

        # Convert the image to base64
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return image_base64

    def initialize(self, initialization_time):
        # Wait for the initialization_time to pass and extract data
        time.sleep(initialization_time)

        self.getData(initialization_time)
        for sensor in self.sensors:
            print(sensor)
            self.createModel(sensor, self.sensorData[sensor]["data"])

        self.initialized = True

    def initializeTSDanalyse(self):

        self.data = self.TSDanalyseInstance.sensorData

        # get list of different sensors
        self.sensors = sorted(list(set(self.data["Sensor"].to_list())))
        for sensor in self.sensors:
            print(sensor)
            self.createModel(sensor, self.sensorData[sensor]["data"])

        self.initialized = True

    def run(self):

        # get self.dbInstance from given name in config
        self.dbInstance = self.parent.getChild(self.dbInstance)

        # get self.TSDanalyse from given name in config if applicable
        if self.TSDanalyse is not None:
            self.TSDanalyseInstance = self.parent.getChild(self.TSDanalyse)

    def configure_router(self):
        @self._router.get("/TSDvisualizer/initialize")
        def initialize(background_tasks: BackgroundTasks, initialization_time: int = 0, TSDanalyse: bool = False, overwrite: bool = False):
            if overwrite is True and self.initialized is True:
                if initialization_time != 0 and TSDanalyse is False:
                    background_tasks.add_task(self.initialize, initialization_time)
                    return {"Status": "Initializing..."}
                elif initialization_time == 0 and TSDanalyse is True:
                    if self.TSDanalyseInstance:
                        background_tasks.add_task(self.initializeTSDanalyse)
                        return {"Status": "Initializing..."}
                    else:
                        return {"Status": "Error! No TSDanalyseInstance given!"}
                else:
                    return {"Status": "Error! Please provide initialization_time or TSDanalyse."}
            elif self.initialized is False:
                if initialization_time != 0 and TSDanalyse is False:
                    background_tasks.add_task(self.initialize, initialization_time)
                    return {"Status": "Initializing..."}
                elif initialization_time == 0 and TSDanalyse is True:
                    if self.TSDanalyseInstance:
                        background_tasks.add_task(self.initializeTSDanalyse)
                        return {"Status": "Initializing..."}
                    else:
                        return {"Status": "Error! No TSDanalyseInstance given!"}
                else:
                    return {"Status": "Error! Please provide initialization_time or TSDanalyse."}
            elif self.initialized is True and overwrite is False:
                return {"Status": "Already initialized. Doing nothing. Set overwrite to true to reinitialize."}

        @self._router.get("/TSDvisualizer/forecast/{sensor}")
        def forecast(sensor):
            if self.initialized is True:
                if sensor in self.sensors:
                    image_base64 = self.forcast(sensor)
                    return StreamingResponse(io.BytesIO(base64.b64decode(image_base64)), media_type="image/png")
                else:
                    return {"Status": "Error! Sensor not found."}
            else:
                return {"Status": "Error! initialize first."}

        @self._router.get("/TSDvisualizer/predict")
        def predict(sensor):
            if self.initialized is True:
                if sensor in self.sensors:
                    msg = self.predict(sensor, plot=False)
                    return msg
                else:
                    return {"Status": "Error! Sensor not found."}
            else:
                return {"Status": "Error! initialize first."}

        @self._router.get("/TSDvisualizer/plot")
        def plot(sensor):
            if self.initialized is True:
                if sensor in self.sensors:
                    image_base64 = self.predict(sensor, plot=True)
                    return StreamingResponse(io.BytesIO(base64.b64decode(image_base64)), media_type="image/png")
                else:
                    return {"Status": "Error! Sensor not found."}
            else:
                return {"Status": "Error! initialize first."}
