from domainwizard.models import ListingIndex, engine

# Create the index
ListingIndex.drop(engine)
ListingIndex.create(engine)
