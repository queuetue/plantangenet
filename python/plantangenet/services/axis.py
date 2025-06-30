#    def get_axis_data(self) -> dict[str, Any]:
#         """Return current timebase data for frame collection."""
#         try:
#             current_time = monotonic()
#             elapsed = current_time - self._start_time

#             # Get accumulator states
#             accumulator_data = {}
#             for name, accum in self._accumulators.items():
#                 accumulator_data[f"accum_{name}"] = {
#                     'value': accum.get_current_count(),
#                     'delta': accum.delta,
#                     'running': accum.running,
#                     'repeating': accum.repeating
#                 }

#             return {
#                 'position': elapsed,
#                 'impulse': {
#                     'timestamp': current_time,
#                     'elapsed_time': elapsed,
#                     'paused': self._paused,
#                     'stepping': self._stepping,
#                     'accumulators': accumulator_data,
#                     'update_interval': current_time - self._last_update_time
#                 },
#                 'metadata': {
#                     'source': 'timebase',
#                     'start_time': self._start_time,
#                     'accumulator_count': len(self._accumulators)
#                 }
#             }
#         except Exception as e:
#             self.logger.error(f"Error getting timebase axis data: {e}")
#             return {
#                 'position': 0.0,
#                 'impulse': {},
#                 'metadata': {
#                     'error': str(e),
#                     'source': 'timebase'
#                 }
#             }

#     def get_axis_name(self) -> str:
#         """Return the axis name for timebase."""
#         return "timebase"
