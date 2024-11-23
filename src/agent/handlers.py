class AgentHandlers:
    async def handle_image_analysis(self, tweet):
        """Handle Picture Perfect Agent functionality"""
        image = await self._extract_image(tweet)
        analysis = await self.image_processor.analyze(image)
        response = await self.llm.generate_response(analysis, "friendly_compliment")
        return response

    async def handle_research(self, tweet):
        """Handle Screenshot + Research Agent functionality"""
        context = await self._gather_thread_context(tweet)
        research = await self._research_topic(context)
        summary = await self.llm.summarize(research)
        return summary 