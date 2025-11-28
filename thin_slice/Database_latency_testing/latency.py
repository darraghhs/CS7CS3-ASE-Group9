import time
import os
from firebase_admin import firestore, credentials, initialize_app


class LatencyTesting:
    """
    This class tests the write and read latency of the firestore database.
    it takes a number of tests as an argument
    and returns the average and max_latency
    """
    def authenticate_firestore(self):
        """Authenticate and return Firestore client."""
        credential_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        cred = credentials.Certificate(credential_path)
        initialize_app(cred)
        db = firestore.client()
        return db

    def test_firestore_latency(self, num_tests=10):
        """
        Test Firestore write and read latency.

        Args:
            num_tests (int): Number of write and read operations to test
        """
        db = self.authenticate_firestore()

        write_accumulator = 0
        write_max_latency = 0
        read_accumulator = 0
        read_max_latency = 0

        for i in range(num_tests):
            # Write latency test
            doc_ref = db.collection("Time").document()
            start_write = time.time()
            doc_ref.set({"time": time.time()})
            write_time_diff = (time.time() - start_write) * 1000
            print(f"Write Latency: {write_time_diff:.2f}ms")
            write_accumulator += write_time_diff
            if write_max_latency < write_time_diff:
                write_max_latency = write_time_diff

            # Read latency test
            start_read = time.time()
            doc_ref.get()  # Read the document we just wrote
            read_time_diff = (time.time() - start_read) * 1000
            print(f"Read Latency: {read_time_diff:.2f}ms")
            read_accumulator += read_time_diff
            if read_max_latency < read_time_diff:
                read_max_latency = read_time_diff

        write_mean_latency = write_accumulator / num_tests
        read_mean_latency = read_accumulator / num_tests
        
        print(f"\nWrite Results:")
        print(f"Average Write Latency: {write_mean_latency:.2f}ms")
        print(f"Max Write Latency: {write_max_latency:.2f}ms")
        
        print(f"\nRead Results:")
        print(f"Average Read Latency: {read_mean_latency:.2f}ms")
        print(f"Max Read Latency: {read_max_latency:.2f}ms")

        return {
            'write_mean': write_mean_latency,
            'write_max': write_max_latency,
            'read_mean': read_mean_latency,
            'read_max': read_max_latency
        }


if __name__ == "__main__":
    tester = LatencyTesting()
    results = tester.test_firestore_latency(100)