from multiprocessing import Process, Manager
import gps_simulator
import app

if __name__ == "__main__":
    with Manager() as manager:
        plate_queue = manager.Queue()

        flask_process = Process(target=app.run_with_queue, args=(plate_queue,))
        flask_process.start()

        simulation_process = Process(target=gps_simulator.run_simulation, args=(plate_queue,))
        simulation_process.start()

        flask_process.join()
        simulation_process.join()
